import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { assetService, riskService } from '../../services/api';
import SecurityCard from '../common/SecurityCard';
import StatusIndicator from '../common/StatusIndicator';

const AssetDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [asset, setAsset] = useState(null);
  const [riskScore, setRiskScore] = useState(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [assetData, riskData] = await Promise.all([
          assetService.getAsset(Number(id)),
          riskService.getRiskScores({ asset_id: Number(id) })
        ]);
        setAsset(assetData);
        setRiskScore(riskData.risk_scores[0] || null);
      } catch (error) {
        console.error('Error fetching asset details:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const handleStatusUpdate = async (newStatus) => {
    if (!asset) return;
    
    try {
      await assetService.updateAsset(asset.id, { status: newStatus });
      setAsset({ ...asset, status: newStatus });
    } catch (error) {
      console.error('Error updating asset status:', error);
    }
  };

  const handleAction = async () => {
    if (!asset || !action) return;

    try {
      switch (action) {
        case 'isolate':
          await assetService.updateAsset(asset.id, { status: 'isolated' });
          setAsset({ ...asset, status: 'isolated' });
          break;
        case 'scan':
          // Trigger deep scan
          await assetService.updateAsset(asset.id, { status: 'scanning' });
          setAsset({ ...asset, status: 'scanning' });
          break;
        case 'update':
          // Trigger agent update
          await assetService.updateAsset(asset.id, { status: 'updating' });
          setAsset({ ...asset, status: 'updating' });
          break;
      }
    } catch (error) {
      console.error('Error performing action:', error);
    }
  };

  if (loading) {
    return <div className="text-neon-blue animate-pulse">Loading...</div>;
  }

  if (!asset) {
    return <div className="text-neon-blue">Asset not found</div>;
  }

  const riskLevel = riskScore ? 
    riskScore.score > 80 ? 'critical' :
    riskScore.score > 60 ? 'high' :
    riskScore.score > 40 ? 'medium' : 'low'
    : 'low';

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-neon-blue animate-pulse-neon">
          Asset Details: {asset.hostname}
        </h2>
        <button
          onClick={() => navigate('/endpoints')}
          className="cyber-button-blue"
        >
          Back to Endpoints
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SecurityCard
          title="Asset Information"
          severity={riskLevel}
        >
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <StatusIndicator
                status={asset.status === 'active' ? 'healthy' : 'warning'}
                pulse={asset.status === 'active'}
              />
              <span className="text-sm text-neon-blue/60">
                Last seen: {new Date(asset.last_seen).toLocaleString()}
              </span>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-neon-blue/60">IP Address</span>
                <span className="text-neon-blue">{asset.ip_address}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neon-blue/60">OS Type</span>
                <span className="text-neon-blue">{asset.os_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neon-blue/60">Agent Version</span>
                <span className="text-neon-blue">{asset.agent_version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neon-blue/60">Asset Type</span>
                <span className="text-neon-blue">{asset.asset_type}</span>
              </div>
            </div>
          </div>
        </SecurityCard>

        <SecurityCard
          title="Risk Assessment"
          severity={riskLevel}
        >
          {riskScore ? (
            <div className="space-y-4">
              <div className="text-4xl font-bold text-neon-blue">
                {riskScore.score}%
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-neon-blue/60">Vulnerability Score</span>
                  <span className="text-neon-blue">{riskScore.factors.vulnerability_score}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neon-blue/60">Threat Score</span>
                  <span className="text-neon-blue">{riskScore.factors.threat_score}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neon-blue/60">Exposure Score</span>
                  <span className="text-neon-blue">{riskScore.factors.exposure_score}%</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-neon-blue/60">No risk assessment available</div>
          )}
        </SecurityCard>

        <SecurityCard
          title="Actions"
          severity={riskLevel}
        >
          <div className="space-y-4">
            <select
              className="cyber-select w-full"
              value={action}
              onChange={(e) => setAction(e.target.value)}
              aria-label="Select action"
            >
              <option value="">Select an action</option>
              <option value="isolate">Isolate Asset</option>
              <option value="scan">Run Deep Scan</option>
              <option value="update">Update Agent</option>
            </select>

            <button
              onClick={handleAction}
              disabled={!action}
              className="cyber-button-purple w-full"
            >
              Execute Action
            </button>
          </div>
        </SecurityCard>

        <SecurityCard
          title="Status Management"
          severity={riskLevel}
        >
          <div className="space-y-4">
            <select
              className="cyber-select w-full"
              value={asset.status}
              onChange={(e) => handleStatusUpdate(e.target.value)}
              aria-label="Update status"
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="maintenance">Maintenance</option>
              <option value="isolated">Isolated</option>
            </select>
          </div>
        </SecurityCard>
      </div>
    </div>
  );
};

export default AssetDetails; 