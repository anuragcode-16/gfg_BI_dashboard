// src/components/ChatInterface.jsx
import { useState } from 'react';
import ChartRenderer from './ChartRenderer';

function LoadingDots() {
    return (
        <div className="loading-dots">
            <span></span><span></span><span></span>
        </div>
    );
}

function SqlExpander({ sql }) {
    const [open, setOpen] = useState(false);
    if (!sql) return null;
    return (
        <div className="sql-expander">
            <button className="sql-expander-btn" onClick={() => setOpen(!open)}>
                {open ? '▾' : '▸'} {open ? 'Hide' : 'View'} SQL Query
            </button>
            {open && <pre className="sql-code">{sql}</pre>}
        </div>
    );
}

export default function ChatInterface({ messages, isLoading }) {
    return (
        <div className="chat-container">
            {messages.map((msg, i) => (
                <div key={i} className={`message message--${msg.role}`}>
                    {msg.role === 'user' ? (
                        <div className="message-bubble message-bubble--user">{msg.content}</div>
                    ) : (
                        <>
                            {msg.error ? (
                                <div className="message-bubble message-bubble--assistant message-bubble--error">
                                    {msg.error}
                                </div>
                            ) : msg.text ? (
                                <div className="message-bubble message-bubble--assistant">{msg.text}</div>
                            ) : null}

                            <SqlExpander sql={msg.sql} />

                            {msg.data && msg.visualization && (
                                <ChartRenderer
                                    data={msg.data}
                                    columns={msg.columns}
                                    visualization={msg.visualization}
                                />
                            )}
                        </>
                    )}
                </div>
            ))}

            {isLoading && (
                <div className="message message--assistant">
                    <div className="message-bubble message-bubble--assistant">
                        <LoadingDots />
                    </div>
                </div>
            )}
        </div>
    );
}
