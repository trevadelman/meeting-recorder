import { createGlobalStyle, css } from 'styled-components';

interface GlobalStylesProps {
  darkMode: boolean;
}

export const GlobalStyles = createGlobalStyle<GlobalStylesProps>`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  html, body {
    height: 100%;
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background-color: ${({ darkMode }) => (darkMode ? '#141414' : '#f0f2f5')};
    color: ${({ darkMode }) => (darkMode ? 'rgba(255, 255, 255, 0.85)' : 'rgba(0, 0, 0, 0.85)')};
  }

  #root {
    height: 100%;
  }

  a {
    color: inherit;
    text-decoration: none;
  }

  /* Ant Design overrides */
  .ant-layout {
    background: ${({ darkMode }) => (darkMode ? '#141414' : '#f0f2f5')};
  }

  .ant-layout-sider {
    background: ${({ darkMode }) => (darkMode ? '#1f1f1f' : '#001529')};
  }

  .ant-layout-header {
    background: ${({ darkMode }) => (darkMode ? '#1f1f1f' : '#fff')};
  }

  .ant-card {
    background: ${({ darkMode }) => (darkMode ? '#1f1f1f' : '#fff')};
    box-shadow: ${({ darkMode }) =>
      darkMode
        ? '0 1px 2px 0 rgba(0, 0, 0, 0.3)'
        : '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)'};
  }

  .ant-table {
    .ant-table-thead > tr > th {
      background: ${({ darkMode }) => (darkMode ? '#1f1f1f' : '#fafafa')};
      &::before {
        display: none;
      }
    }
  }

  /* Scrollbar styling */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: ${({ darkMode }) => (darkMode ? '#141414' : '#f1f1f1')};
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb {
    background: ${({ darkMode }) => (darkMode ? '#434343' : '#888')};
    border-radius: 4px;
    &:hover {
      background: ${({ darkMode }) => (darkMode ? '#595959' : '#555')};
    }
  }

  /* Typography */
  h1 {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 24px;
  }

  h2 {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 20px;
  }

  h3 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
  }

  /* Utility classes */
  .text-center {
    text-align: center;
  }

  .text-right {
    text-align: right;
  }

  .text-left {
    text-align: left;
  }

  .flex {
    display: flex;
  }

  .flex-col {
    flex-direction: column;
  }

  .items-center {
    align-items: center;
  }

  .justify-center {
    justify-content: center;
  }

  .justify-between {
    justify-content: space-between;
  }

  .w-full {
    width: 100%;
  }

  .h-full {
    height: 100%;
  }
`;
