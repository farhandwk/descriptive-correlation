import React,{ useState, useEffect } from 'react'
import './App.css'

function App() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [analysisData, setAnalysisData] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleFileChange = (event) => {
    const file = event.target.files[0]
    if (file) {
      console.log("file dipilih:", file)
      setSelectedFile(file)
      // Reset tampilan saat file baru dipilih
      setAnalysisData(null)
      setError('')
    }
  }

  const handleAnalysis = async (event) => {
    event.preventDefault()
    console.log("Tombol 'Analisis' ditekan, memulai proses.");
    if (!selectedFile) {
      console.log("Gagal: Tidak ada file yang dipilih saat submit.");
      setError('Silahkan pilih file terlebih dahulu')
      return
    }

    setIsLoading(true)
    setError('')
    setAnalysisData(null)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const apiUrl = `${import.meta.env.VITE_API_URL || ''}/api/upload`;
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json()

      // TAMBAHKAN LOG INI UNTUK MELIHAT ISI DATA
      console.log("Data diterima dari backend:", data);

      if (!response.ok) {
        throw new Error(data.error || 'Terjadi kesalahan pada server.')
      }

      setAnalysisData(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  console.log('Nilai AnalysisData:', analysisData)

  
  return (
    <div className="container">
      <div className="card">
        <h1 className="title">Analisis Deskriptif Interaktif</h1>
        
        <form onSubmit={handleAnalysis}>
          <div className="upload-section">
            <input type="file" onChange={handleFileChange} accept=".csv" />
            
            {/* TAMBAHKAN onClick DI SINI UNTUK DEBUGGING */}
            <button 
              type="submit" 
              disabled={isLoading}
              onClick={() => console.log("Button Clicked!")}
            >
              {isLoading ? 'Menganalisis...' : 'Analisis Sekarang'}
            </button>
          </div>
        </form>

        {error && <p className="error-message">{error}</p>}
          {analysisData && (
          <div className="results-section">
            
            {/* Bagian Info File dan Statistik */}
            <p className="filename">File: <strong>{analysisData.nama_file}</strong></p>
            <div className="info">
              <span>Baris: <strong>{analysisData.jumlah_baris}</strong></span>
              <span>Kolom: <strong>{analysisData.jumlah_kolom}</strong></span>
            </div>
            <h2 className="subtitle">Statistik per Kolom</h2>
            {Object.entries(analysisData.statistik).map(([kolom, stats]) => (
              <div key={kolom} className="stats-block">
                <h3 className="column-title">{kolom}</h3>
                <ul className="stats-list">
                  {Object.entries(stats).map(([key, value]) => (
                    <li key={key}>
                      <span>{key}</span>
                      <strong>{Number(value).toFixed(2)}</strong>
                    </li>
                  ))}
                </ul>
              </div>
            ))}

            {/* Bagian Heatmap (TERMASUK LEGENDA DI DALAMNYA) */}
            {analysisData.heatmap_base64 && (
              <div className="heatmap-container">
                <h2 className="subtitle">Heatmap Korelasi</h2>
                <p>Visualisasi matriks korelasi untuk melihat hubungan antar variabel.</p>
                
                {/* LEGENDA SEKARANG ADA DI SINI */}
                {analysisData.pemetaan_kolom && (
                    <div className="legend-section">
                        <h4>Legenda:</h4>
                        <ul className="legend-list">
                            {Object.entries(analysisData.pemetaan_kolom).map(([pendek, panjang]) => (
                                <li key={pendek}>
                                    <strong>{pendek}:</strong> {panjang}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                <img 
                  src={`data:image/png;base64,${analysisData.heatmap_base64}`} 
                  alt="Heatmap Korelasi" 
                  className="heatmap-image"
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
