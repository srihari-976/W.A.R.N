import React from 'react';

const ThreatList = ({ threats }) => {
    return (
        <div className="threat-list">
            {threats.length === 0 ? (
                <div className="no-threats">No active threats detected</div>
            ) : (
                threats.map((threat, index) => (
                    <div key={index} className={`threat-item ${threat.risk_level}`}>
                        <div className="threat-header">
                            <span className="threat-type">{threat.type}</span>
                            <span className="threat-score">Score: {threat.score}</span>
                        </div>
                        <div className="threat-details">
                            <p>{threat.details.description}</p>
                            <div className="threat-meta">
                                <span>Source: {threat.source_ip || 'Unknown'}</span>
                                <span>Time: {new Date(threat.timestamp).toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                ))
            )}

            <style jsx>{`
                .threat-list {
                    max-height: 500px;
                    overflow-y: auto;
                }

                .no-threats {
                    text-align: center;
                    padding: 20px;
                    color: #666;
                }

                .threat-item {
                    margin-bottom: 10px;
                    padding: 15px;
                    border-radius: 4px;
                    background: #fff;
                    border-left: 4px solid #ccc;
                }

                .threat-item.high {
                    border-left-color: #f44336;
                }

                .threat-item.medium {
                    border-left-color: #ff9800;
                }

                .threat-item.low {
                    border-left-color: #4CAF50;
                }

                .threat-header {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                }

                .threat-type {
                    font-weight: bold;
                    text-transform: capitalize;
                }

                .threat-score {
                    font-weight: bold;
                }

                .threat-details {
                    font-size: 0.9em;
                }

                .threat-meta {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 10px;
                    font-size: 0.8em;
                    color: #666;
                }
            `}</style>
        </div>
    );
};

export default ThreatList; 