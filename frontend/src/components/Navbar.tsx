"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BookOpen, Sparkles, History, Settings, Info, Cpu, Search, BarChart2 } from 'lucide-react';
import { apiClient } from '@/services/api';

export default function Navbar() {
  const pathname = usePathname();
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [modelName, setModelName] = useState<string>('Google Gemini AI');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await apiClient.get('/health');
        setIsOnline(res.data.database_connected ?? true);
        if (res.data.ai_model) {
          const raw = res.data.ai_model.split('/').pop() || 'Google Gemini AI';
          setModelName(raw);
        }
      } catch (err) {
        setIsOnline(false);
      }
    };
    checkHealth();
  }, []);

  const navLinks = [
    { name: 'Workspace', href: '/', icon: Sparkles },
    { name: 'History', href: '/history', icon: History },
    { name: 'DB Schema', href: '/settings', icon: Settings },
    { name: 'Benchmarks', href: '/benchmarks', icon: BarChart2 },
    { name: 'About', href: '/about', icon: Info },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#141413]/90 backdrop-blur-md border-b border-[#2b2b27] px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand Logo - Claude Terracotta Mark */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-lg bg-[#d97757] flex items-center justify-center shadow-md shadow-[#d97757]/20 group-hover:bg-[#e28363] transition-colors">
            {/* Claude Spark Pictogram SVG */}
            <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L14.8 9.2L22 12L14.8 14.8L12 22L9.2 14.8L2 12L9.2 9.2L12 2Z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-[#f3f3ee] tracking-tight group-hover:text-[#f4a284] transition-colors">
                Text2SQL
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full badge-terracotta font-semibold uppercase tracking-wider">
                Gemini AI
              </span>
            </div>
            <p className="text-[11px] text-[#a1a19a]">PostgreSQL • Google Gemini 3.6 Flash</p>
          </div>
        </Link>


        {/* Navigation Links */}
        <nav className="hidden md:flex items-center space-x-1 bg-[#1c1c1a] p-1 rounded-xl border border-[#2b2b27]">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-[#282824] text-[#f4a284] border border-[#3d3d37] shadow-sm'
                    : 'text-[#a1a19a] hover:text-[#f3f3ee] hover:bg-[#242421]'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#d97757]' : ''}`} />
                <span>{link.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Status Badges */}
        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#1c1c1a] border border-[#2b2b27] text-xs">
            <Cpu className="w-3.5 h-3.5 text-[#d97757]" />
            <span className="text-[#a1a19a] font-mono font-medium text-[11px]">{modelName}</span>
          </div>

          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#1c1c1a] border border-[#2b2b27] text-xs">
            <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className={isOnline ? 'text-emerald-400 font-medium text-[11px]' : 'text-rose-400 font-medium text-[11px]'}>
              {isOnline ? 'PostgreSQL Active' : 'Offline'}
            </span>
          </div>
        </div>

      </div>
    </header>
  );
}

