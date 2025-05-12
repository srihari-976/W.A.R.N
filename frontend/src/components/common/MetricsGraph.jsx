import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Neon color map
const colorMap = {
  blue: '#00ffff',    // Neon blue
  red: '#ff007f',     // Neon pink/red
  green: '#39ff14',   // Neon green
  yellow: '#fff700',  // Neon yellow
  purple: '#a020f0',  // Neon purple
};

const MetricsGraph = ({ title, data, labels, color = 'blue' }) => {
  const lineColor = colorMap[color] || colorMap.blue;
  const fillColor = lineColor + '33'; // 20% opacity in hex

  const chartData = {
    labels,
    datasets: [
      {
        label: title,
        data,
        borderColor: lineColor,
        backgroundColor: fillColor,
        borderWidth: 2,
        pointBackgroundColor: lineColor,
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        tension: 0.4,
        fill: true
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: lineColor,
        borderWidth: 1,
        padding: 12,
        displayColors: false,
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${context.parsed.y}`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          color: lineColor + '22',
          drawBorder: false
        },
        ticks: {
          color: lineColor,
          font: {
            size: 12,
            weight: '500'
          },
          padding: 10
        }
      },
      y: {
        grid: {
          color: lineColor + '22',
          drawBorder: false
        },
        ticks: {
          color: lineColor,
          font: {
            size: 12,
            weight: '500'
          },
          padding: 10
        },
        beginAtZero: true
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    },
    animation: {
      duration: 1000,
      easing: 'easeInOutQuart'
    }
  };

  return (
    <div className="space-y-4 bg-black/30 p-6 rounded-lg border border-neon-blue/20 backdrop-blur-sm">
      <h3 className="text-xl font-bold text-neon-blue flex items-center gap-2">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: lineColor }}></span>
        {title}
      </h3>
      <div className="h-72">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
};

export default MetricsGraph; 