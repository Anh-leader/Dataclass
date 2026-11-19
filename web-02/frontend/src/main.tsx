import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './styles/tokens.css'
import './styles.css'
import './styles/peer-learning.css'
import './styles/exam-review.css'
import './styles/ai-comparison.css'
import './styles/readability.css'
import './styles/community.css'
import './styles/theme.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><BrowserRouter><App /></BrowserRouter></React.StrictMode>,
)
