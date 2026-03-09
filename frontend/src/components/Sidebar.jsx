// src/components/Sidebar.jsx
import { useState, useRef } from 'react';

const DEFAULT_QUERIES = [
    'Show total claims paid by insurer for 2021-22',
    'What is the trend of claims intimated over time?',
    'Top 5 insurers by claim settlement ratio',
    'Compare HDFC and ICICI paid amounts',
    'Which providers show the highest rejection rate?',
    'Distribution of claims by category',
];

const UPLOADED_QUERIES = [
    'Show me the first 10 rows of the dataset',
    'What is the total count of records?',
    'Provide a summary of the numerical columns',
    'List the unique categories in the dataset',
    'What are the top 5 highest values?',
];

export default function Sidebar({ onQuery, isUploaded, onUpload, onReset, onClearHistory }) {
    const [uploading, setUploading] = useState(false);
    const fileRef = useRef(null);

    const queries = isUploaded ? UPLOADED_QUERIES : DEFAULT_QUERIES;

    const handleFileChange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setUploading(true);
        try {
            await onUpload(file);
        } finally {
            setUploading(false);
            if (fileRef.current) fileRef.current.value = '';
        }
    };

    return (
        <aside className="app-sidebar">
            {/* Brand */}
            <div className="sidebar-brand">
                <img src="/logo.png" alt="InsightAI Logo" className="sidebar-brand-icon" style={{ width: 32, height: 32, objectFit: 'contain' }} />
                <div className="sidebar-brand-text">
                    <h2>InsightAI</h2>
                    <p>Data Intelligence</p>
                </div>
            </div>

            {/* Data Status */}
            <div>
                <p className="sidebar-section-title">Data Source</p>
                <div className="sidebar-data-badge">
                    {isUploaded ? 'Custom Dataset Active' : 'Insurance Claims Data'}
                </div>
                {isUploaded && (
                    <button className="sidebar-btn sidebar-btn--danger" style={{ marginTop: 8 }} onClick={onReset}>
                        ↩ Revert to Default
                    </button>
                )}
            </div>

            <hr className="sidebar-divider" />

            {/* Upload */}
            <div>
                <p className="sidebar-section-title">Upload Data</p>
                <div className="upload-zone">
                    <input type="file" accept=".csv" ref={fileRef} onChange={handleFileChange} />
                    <div className="upload-zone-icon"></div>
                    <div className="upload-zone-text">
                        {uploading ? 'Processing...' : <><span>Click to upload</span> a CSV file</>}
                    </div>
                </div>
            </div>

            <hr className="sidebar-divider" />

            {/* Suggested Queries */}
            <div style={{ flex: 1 }}>
                <p className="sidebar-section-title">Suggested Queries</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {queries.map((q) => (
                        <button key={q} className="query-chip" onClick={() => onQuery(q)}>
                            {q}
                        </button>
                    ))}
                </div>
            </div>

            <hr className="sidebar-divider" />

            {/* Actions */}
            <button className="sidebar-btn" onClick={onClearHistory}>
                Clear Session
            </button>
        </aside>
    );
}
