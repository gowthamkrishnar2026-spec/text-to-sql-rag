"use client";

import React, { useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import { BarChart3, LineChart as LineIcon, PieChart as PieIcon, AreaChart as AreaIcon } from 'lucide-react';

interface VisualizerProps {
  columns: string[];
  rows: Record<string, any>[];
  visualizationConfig?: {
    recommended_chart: 'bar' | 'pie' | 'line' | 'area' | 'table';
    x_axis: string;
    y_axis: string[];
    numeric_columns: string[];
    string_columns: string[];
  };
}

const COLORS = ['#d97757', '#52a373', '#4f80e1', '#a066d9', '#e5a83b', '#38bdf8', '#f472b6'];

export default function Visualizer({ columns, rows, visualizationConfig }: VisualizerProps) {
  const [chartType, setChartType] = useState<'bar' | 'line' | 'pie' | 'area'>(
    (visualizationConfig?.recommended_chart as any) || 'bar'
  );

  if (!rows || rows.length === 0 || !columns || columns.length === 0) {
    return null;
  }

  // Determine X Axis and Y Axes
  const xAxisKey = visualizationConfig?.x_axis || columns.find((c) => typeof rows[0][c] === 'string') || columns[0];
  const yAxisKeys = visualizationConfig?.y_axis?.length
    ? visualizationConfig.y_axis
    : columns.filter((c) => c !== xAxisKey && typeof rows[0][c] === 'number');

  if (yAxisKeys.length === 0) {
    return (
      <div className="w-full claude-card p-6 text-center text-[#a1a19a]">
        <p className="text-xs">No numeric column found to render visual charts.</p>
      </div>
    );
  }

  return (
    <div className="w-full claude-card p-5 shadow-xl flex flex-col h-full">
      
      {/* Header with chart tabs */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#2b2b27]">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-4 h-4 text-[#d97757]" />
          <h3 className="font-semibold text-[#f3f3ee] text-sm">Visual Analytics</h3>
        </div>

        {/* Chart type switchers */}
        <div className="flex items-center space-x-1 bg-[#111110] p-1 rounded-lg border border-[#282824]">
          <button
            onClick={() => setChartType('bar')}
            className={`p-1.5 rounded-md text-xs flex items-center space-x-1 transition-all ${
              chartType === 'bar' ? 'bg-[#d97757] text-white font-medium shadow-sm' : 'text-[#a1a19a] hover:text-[#f3f3ee]'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Bar</span>
          </button>

          <button
            onClick={() => setChartType('line')}
            className={`p-1.5 rounded-md text-xs flex items-center space-x-1 transition-all ${
              chartType === 'line' ? 'bg-[#d97757] text-white font-medium shadow-sm' : 'text-[#a1a19a] hover:text-[#f3f3ee]'
            }`}
          >
            <LineIcon className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Line</span>
          </button>

          <button
            onClick={() => setChartType('pie')}
            className={`p-1.5 rounded-md text-xs flex items-center space-x-1 transition-all ${
              chartType === 'pie' ? 'bg-[#d97757] text-white font-medium shadow-sm' : 'text-[#a1a19a] hover:text-[#f3f3ee]'
            }`}
          >
            <PieIcon className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Pie</span>
          </button>

          <button
            onClick={() => setChartType('area')}
            className={`p-1.5 rounded-md text-xs flex items-center space-x-1 transition-all ${
              chartType === 'area' ? 'bg-[#d97757] text-white font-medium shadow-sm' : 'text-[#a1a19a] hover:text-[#f3f3ee]'
            }`}
          >
            <AreaIcon className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Area</span>
          </button>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="w-full h-80 min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'bar' ? (
            <BarChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#282824" opacity={0.6} />
              <XAxis dataKey={xAxisKey} stroke="#a1a19a" fontSize={11} />
              <YAxis stroke="#a1a19a" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111110', borderColor: '#33332f', borderRadius: '0.5rem', color: '#f3f3ee' }}
              />
              <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px', color: '#a1a19a' }} />
              {yAxisKeys.map((yKey, idx) => (
                <Bar key={yKey} dataKey={yKey} fill={COLORS[idx % COLORS.length]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          ) : chartType === 'line' ? (
            <LineChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#282824" opacity={0.6} />
              <XAxis dataKey={xAxisKey} stroke="#a1a19a" fontSize={11} />
              <YAxis stroke="#a1a19a" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111110', borderColor: '#33332f', borderRadius: '0.5rem', color: '#f3f3ee' }}
              />
              <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px', color: '#a1a19a' }} />
              {yAxisKeys.map((yKey, idx) => (
                <Line key={yKey} type="monotone" dataKey={yKey} stroke={COLORS[idx % COLORS.length]} strokeWidth={2.5} dot={{ r: 4 }} />
              ))}
            </LineChart>
          ) : chartType === 'area' ? (
            <AreaChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#282824" opacity={0.6} />
              <XAxis dataKey={xAxisKey} stroke="#a1a19a" fontSize={11} />
              <YAxis stroke="#a1a19a" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111110', borderColor: '#33332f', borderRadius: '0.5rem', color: '#f3f3ee' }}
              />
              <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px', color: '#a1a19a' }} />
              {yAxisKeys.map((yKey, idx) => (
                <Area
                  key={yKey}
                  type="monotone"
                  dataKey={yKey}
                  stroke={COLORS[idx % COLORS.length]}
                  fill={COLORS[idx % COLORS.length]}
                  fillOpacity={0.25}
                />
              ))}
            </AreaChart>
          ) : (
            <PieChart>
              <Tooltip
                contentStyle={{ backgroundColor: '#111110', borderColor: '#33332f', borderRadius: '0.5rem', color: '#f3f3ee' }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', color: '#a1a19a' }} />
              <Pie
                data={rows}
                dataKey={yAxisKeys[0]}
                nameKey={xAxisKey}
                cx="50%"
                cy="50%"
                outerRadius={95}
                label
              >
                {rows.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

