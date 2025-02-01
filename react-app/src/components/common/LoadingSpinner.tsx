import { Spin } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import styled from 'styled-components';

const SpinnerWrapper = styled.div<{ fullPage?: boolean }>`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: ${({ fullPage }) => (fullPage ? '0' : '48px')};
  ${({ fullPage }) =>
    fullPage &&
    `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.85);
    z-index: 1000;
  `}
`;

const StyledSpin = styled(Spin)`
  .ant-spin-dot {
    font-size: 24px;
  }
`;

interface LoadingSpinnerProps {
  fullPage?: boolean;
  size?: number;
  tip?: string;
}

export function LoadingSpinner({ fullPage, size = 40, tip }: LoadingSpinnerProps) {
  const antIcon = <LoadingOutlined style={{ fontSize: size }} spin />;

  return (
    <SpinnerWrapper fullPage={fullPage}>
      <StyledSpin indicator={antIcon} tip={tip} />
    </SpinnerWrapper>
  );
}
