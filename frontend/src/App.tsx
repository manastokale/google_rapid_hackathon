import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Actions } from './pages/Actions'
import { Chat } from './pages/Chat'
import { Connectors } from './pages/Connectors'
import { Dashboard } from './pages/Dashboard'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/actions" element={<Actions />} />
          <Route path="/connectors" element={<Connectors />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

