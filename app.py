from flask import Flask, render_template, jsonify, request, send_file, session, current_app, redirect
import wave
import io
import numpy as np
from markupsafe import Markup  # Changed this line
from core import MeetingRecorder
from config import FlaskConfig, ERROR_MESSAGES, EXPORT_FORMATS
import threading
from datetime import datetime
import os
from pathlib import Path
import markdown
import sqlite3

app = Flask(__name__, static_url_path='/static')
app.config.from_object(FlaskConfig)

# Ensure static directories exist
for dir_name in ['static', 'static/js']:
    path = Path(dir_name)
    path.mkdir(exist_ok=True)

# Initialize recorder and state management
recorder = MeetingRecorder()
recording_state = {
    'thread': None,
    'current_meeting': None,
    'status': 'idle',
    'progress': None,
    'selected_device': None
}

# Context processor for template variables
@app.context_processor
def utility_processor():
    return {
        'now': datetime.now()
    }

@app.template_filter('markdown')
def markdown_filter(text):
    """Convert markdown text to HTML"""
    if not text:
        return ''
    return Markup(markdown.markdown(text))

def status_callback(message):
    """Callback for updating recording progress"""
    recording_state['progress'] = message

@app.route('/upload_recording', methods=['POST'])
def upload_recording():
    """Handle uploaded recording from client"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio']
        title = request.form.get('title', '')
        duration = float(request.form.get('duration', 0))
        
        # Convert audio data to format expected by core.py
        audio_data = io.BytesIO(audio_file.read())
        with wave.open(audio_data, 'rb') as wf:
            audio_array = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            sample_rate = wf.getframerate()
        
        # Process the recording
        meeting = recorder.record_meeting(
            duration=duration,
            title=title,
            audio_data=(audio_array, sample_rate)
        )
        
        return jsonify({
            'message': 'Recording uploaded successfully',
            'meeting_id': meeting.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices')
def list_devices():
    """Get list of available input devices"""
    try:
        devices = recorder.audio_processor.list_input_devices()
        if not devices:
            return jsonify({'error': ERROR_MESSAGES['no_devices']}), 404
        return jsonify({'devices': devices})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/select', methods=['POST'])
def select_device():
    """Select input device for recording"""
    try:
        device_id = request.json.get('device_id')
        if device_id is not None:
            if recorder.audio_processor.set_input_device(device_id):
                recording_state['selected_device'] = device_id
                return jsonify({'message': 'Device selected successfully'})
            return jsonify({'error': ERROR_MESSAGES['device_error']}), 400
        return jsonify({'error': 'No device ID provided'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """Main page - list all meetings"""
    meetings = recorder.db.get_all_meetings()
    devices = recorder.audio_processor.list_input_devices()
    return render_template('index.html', 
                         meetings=meetings,
                         recording_state=recording_state,
                         devices=devices)

@app.route('/start_recording', methods=['POST'])
def start_recording():
    """Start a new recording"""
    if recording_state['thread'] and recording_state['thread'].is_alive():
        return jsonify({
            'error': ERROR_MESSAGES['recording_in_progress']
        }), 400
    
    try:
        duration = int(request.form.get('duration', FlaskConfig.DEFAULT_RECORDING_DURATION))
        if not FlaskConfig.MIN_RECORDING_DURATION <= duration <= FlaskConfig.MAX_RECORDING_DURATION:
            return jsonify({
                'error': ERROR_MESSAGES['invalid_duration']
            }), 400
        
        title = request.form.get('title', '')
        
        def record():
            try:
                recording_state['status'] = 'recording'
                recording_state['current_meeting'] = recorder.record_meeting(
                    duration, 
                    title,
                    status_callback
                )
                recording_state['status'] = 'complete'
            except Exception as e:
                recording_state['status'] = 'error'
                recording_state['progress'] = str(e)
        
        recording_state['thread'] = threading.Thread(target=record)
        recording_state['thread'].start()
        
        return jsonify({
            'message': 'Recording started',
            'duration': duration
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recording_status')
def recording_status():
    """Get current recording status"""
    return jsonify({
        'status': recording_state['status'],
        'progress': recording_state['progress'],
        'meeting_id': recording_state['current_meeting'].id if recording_state['current_meeting'] else None
    })

@app.route('/meeting/<meeting_id>')
def meeting_detail(meeting_id):
    """Show details for a specific meeting"""
    meeting = recorder.db.get_meeting(meeting_id)
    if not meeting:
        return render_template('error.html', 
                             message=ERROR_MESSAGES['meeting_not_found']), 404
    
    return render_template('meeting_detail.html', meeting=meeting)

@app.route('/export/<meeting_id>')
def export_meeting(meeting_id):
    """Export meeting in specified format"""
    format = request.args.get('format', 'txt')
    if format not in EXPORT_FORMATS:
        return jsonify({'error': 'Invalid export format'}), 400
    
    try:
        filepath = recorder.export_meeting(meeting_id, format)
        return send_file(
            filepath,
            mimetype=EXPORT_FORMATS[format]['mime_type'],
            as_attachment=True,
            download_name=os.path.basename(filepath)
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/audio/<meeting_id>')
def get_audio(meeting_id):
    """Stream meeting audio file"""
    meeting = recorder.db.get_meeting(meeting_id)
    if not meeting or not os.path.exists(meeting.audio_path):
        return jsonify({'error': ERROR_MESSAGES['meeting_not_found']}), 404
    
    return send_file(
        meeting.audio_path,
        mimetype='audio/wav'
    )

@app.route('/delete/<meeting_id>', methods=['POST'])
def delete_meeting(meeting_id):
    """Delete a meeting and its associated files"""
    meeting = recorder.db.get_meeting(meeting_id)
    if not meeting:
        return jsonify({'error': ERROR_MESSAGES['meeting_not_found']}), 404
    
    try:
        # Delete audio file
        if os.path.exists(meeting.audio_path):
            os.remove(meeting.audio_path)
        
        # Delete any exports
        export_pattern = f"meeting_*_{meeting.id[:8]}.*"
        for export_file in Path('exports').glob(export_pattern):
            export_file.unlink()
        
        # Delete from database
        with sqlite3.connect(recorder.db.db_path) as conn:
            conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            conn.commit()
        
        return jsonify({'message': 'Meeting deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.template_filter('format_duration')
def format_duration(seconds):
    """Format duration in seconds to human readable string"""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

@app.template_filter('format_datetime')
def format_datetime(dt):
    """Format datetime object to human readable string"""
    return dt.strftime("%B %d, %Y %I:%M %p")

if __name__ == '__main__':
    import socket

    def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 1))  # Doesn't actually connect
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    try:
        # Check if certificate files exist
        cert_path = Path('cert.pem')
        key_path = Path('key.pem')
        
        if not cert_path.exists() or not key_path.exists():
            print("\nGenerating new certificates...")
            from generate_cert import generate_self_signed_cert
            generate_self_signed_cert()
            print("Certificates generated successfully!")

        ip_address = get_ip()
        port = 5002

        print("\nStarting server...")
        print("You can access the application at:")
        print(f"  * Local:   https://localhost:{port}")
        print(f"  * Network: https://{ip_address}:{port}")
        print("\nNote: You will need to accept the security warning in your browser")
        print("since we're using a self-signed certificate.")
        print("\nPress CTRL+C to quit\n")

        ssl_context = ('cert.pem', 'key.pem')
        app.run(host='0.0.0.0', port=port, ssl_context=ssl_context, debug=False)

    except Exception as e:
        print(f"\nError starting HTTPS server: {e}")
        print("Starting without SSL...")
        app.run(host='0.0.0.0', port=5002, debug=False)
