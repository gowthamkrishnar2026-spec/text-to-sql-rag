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

const COLORS = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EC4899', '#06B6D4', '#6366F1'];

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
      <div className="w-full glass-panel rounded-2xl p-6 text-center text-slate-400 border border-slate-800">
        <p className="text-sm">No numeric column found to render visual charts.</p>
      </div>
    );
  }

  return (
    <div className="w-full glass-panel rounded-2xl p-5 shadow-xl border border-slate-800 flex flex-col h-full">
      
      {/* Header with chart tabs */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-purple-400" />
          <h3 className="font-semibold text-white text-base">Data Analytics & Chart</h3>
        </div>

        {/* Chart type switchers */}
        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setChartType('bar')}
            className={`p-1.5 rounded-lg text-xs flex items-center space-x-1 transition-all ${
              chartType === 'bar' ? 'bg-purple-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span className="hidden sm:inline">Bar</span>
          </button>

          <button
            onClick={() => setChartType('line')}
            className={`p-1.5 rounded-lg text-xs flex items-center space-x-1 transition-all ${
              chartType === 'line' ? 'bg-purple-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <LineIcon className="w-4 h-4" />
            <span className="hidden sm:inline">Line</span>
          </button>

          <button
            onClick={() => setChartType('pie')}
            className={`p-1.5 rounded-lg text-xs flex items-center space-x-1 transition-all ${
              chartType === 'pie' ? 'bg-purple-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <PieIcon className="w-4 h-4" />
            <span className="hidden sm:inline">Pie</span>
          </button>

          <button
            onClick={() => setChartType('area')}
            className={`p-1.5 rounded-lg text-xs flex items-center space-x-1 transition-all ${
              chartType === 'area' ? 'bg-purple-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <AreaIcon className="w-4 h-4" />
            <span className="hidden sm:inline">Area</span>
          </button>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="w-full h-80 min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'bar' ? (
            <BarChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
              <XAxis dataKey={xAxisKey} stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#fff' }}
              />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {yAxisKeys.map((yKey, idx) => (
                <Bar key={yKey} dataKey={yKey} fill={COLORS[idx % COLORS.length]} radius={[6, 6, 0, 0]} />
              ))}
            </BarChart>
          ) : chartType === 'line' ? (
            <LineChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
              <XAxis dataKey={xAxisKey} stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#fff' }}
              />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {yAxisKeys.map((yKey, idx) => (
                <Line key={yKey} type="monotone" dataKey={yKey} stroke={COLORS[idx % COLORS.length]} strokeWidth={3} dot={{ r: 4 }} />
              ))}
            </LineChart>
          ) : chartType === 'area' ? (
            <AreaChart data={rows} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
              <XAxis dataKey={xAxisKey} stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#fff' }}
              />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
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
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#fff' }}
              />
              <Legend />
              <Pie
                data={rows}
                dataKey={yAxisKeys[0]}
                nameKey={xAxisKey}
                cx="50%"
                cy="50%"
                outerRadius={100}
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
