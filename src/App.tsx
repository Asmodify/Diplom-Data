/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { DataSources } from './components/DataSources';
import { PredictiveAnalysis } from './components/PredictiveAnalysis';
import { AdminControl } from './components/AdminControl';
import { LayoutDashboard, Database, LineChart, Settings, LogOut, Shield } from 'lucide-react';
import { cn } from './lib/utils';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const navItems = [
    { id: 'dashboard', label: 'Хянах самбар', icon: LayoutDashboard },
    { id: 'sources', label: 'Өгөгдлийн эх сурвалж', icon: Database },
    { id: 'analysis', label: 'Таамаглалт шинжилгээ', icon: LineChart },
    { id: 'admin', label: 'Админ удирдлага', icon: Shield },
    { id: 'settings', label: 'Тохиргоо', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-gray-50/50">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-white flex flex-col">
        <div className="h-16 flex items-center px-6 border-b">
          <h1 className="font-bold text-lg text-indigo-600 flex items-center gap-2">
            <LineChart className="h-5 w-5" />
            Мэдээлэл Анализ
          </h1>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                  activeTab === item.id
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                )}
              >
                <Icon className={cn("h-5 w-5", activeTab === item.id ? "text-indigo-700" : "text-gray-400")} />
                {item.label}
              </button>
            );
          })}
        </nav>
        <div className="p-4 border-t">
          <button className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-md transition-colors">
            <LogOut className="h-5 w-5 text-gray-400" />
            Гарах
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <header className="h-16 flex items-center justify-between px-8 border-b bg-white">
          <h2 className="text-xl font-semibold text-gray-800">
            {navItems.find(i => i.id === activeTab)?.label}
          </h2>
          <div className="flex items-center gap-4">
            <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm">
              AD
            </div>
          </div>
        </header>
        <div className="p-8">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'sources' && <DataSources />}
          {activeTab === 'analysis' && <PredictiveAnalysis />}
          {activeTab === 'admin' && <AdminControl />}
          {activeTab === 'settings' && (
            <div className="text-center text-gray-500 mt-20">
              Тохиргооны хэсэг хөгжүүлэгдэж байна...
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
