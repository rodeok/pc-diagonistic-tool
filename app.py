#!/usr/bin/env python3
"""
Advanced PC Diagnostic Tool with GUI and Predictive Analytics
Features: Battery health, RAM analysis, HDD/SSD health, failure prediction,
lifespan estimation, and visual analytics with bar charts
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib
# Explicitly set backend for Tkinter to avoid backend discovery issues in frozen apps
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import psutil
import platform
import subprocess
import sys
import time
import json
import threading
from datetime import datetime, timedelta
import os
import re

class AdvancedDiagnosticGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced PC Hardware Diagnostic Tool")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Data storage
        self.diagnostic_data = {}
        self.health_scores = {}
        self.predictions = {}
        
        # Create GUI
        self.create_widgets()
        self.style_widgets()
        
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Advanced PC Hardware Diagnostic Tool", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Left panel - Controls
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Scan button
        self.scan_button = ttk.Button(control_frame, text="Start Full Scan", 
                                     command=self.start_scan, style="Accent.TButton")
        self.scan_button.pack(pady=5, fill=tk.X)
        
        # Progress bar
        self.progress = ttk.Progressbar(control_frame, mode='determinate')
        self.progress.pack(pady=5, fill=tk.X)
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Ready to scan")
        self.status_label.pack(pady=5)
        
        # Component selection
        ttk.Label(control_frame, text="Select Components:").pack(pady=(15, 5))
        
        self.check_vars = {
            'battery': tk.BooleanVar(value=True),
            'memory': tk.BooleanVar(value=True),
            'storage': tk.BooleanVar(value=True),
            'temperature': tk.BooleanVar(value=True),
            'performance': tk.BooleanVar(value=True)
        }
        
        for component, var in self.check_vars.items():
            ttk.Checkbutton(control_frame, text=component.title(), 
                           variable=var).pack(anchor=tk.W)
        
        # Health Summary
        health_frame = ttk.LabelFrame(control_frame, text="Health Summary", padding="10")
        health_frame.pack(pady=10, fill=tk.X)
        
        self.health_text = tk.Text(health_frame, height=8, width=30, 
                                  font=('Courier', 9))
        self.health_text.pack(fill=tk.BOTH)
        
        # Right panel - Tabbed interface
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.create_overview_tab()
        self.create_analytics_tab()
        self.create_details_tab()
        self.create_predictions_tab()
        
    def create_overview_tab(self):
        """Create overview tab with system information"""
        overview_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(overview_frame, text="Overview")
        
        # System info
        sys_frame = ttk.LabelFrame(overview_frame, text="System Information", padding="10")
        sys_frame.pack(fill=tk.X, pady=5)
        
        self.sys_info_text = tk.Text(sys_frame, height=6, font=('Courier', 9))
        self.sys_info_text.pack(fill=tk.BOTH)
        
        # Component status
        status_frame = ttk.LabelFrame(overview_frame, text="Component Status", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.status_tree = ttk.Treeview(status_frame, columns=('Health', 'Status', 'Details'), 
                                       show='tree headings', height=12)
        self.status_tree.heading('#0', text='Component')
        self.status_tree.heading('Health', text='Health %')
        self.status_tree.heading('Status', text='Status')
        self.status_tree.heading('Details', text='Details')
        
        self.status_tree.column('#0', width=150)
        self.status_tree.column('Health', width=80)
        self.status_tree.column('Status', width=100)
        self.status_tree.column('Details', width=200)
        
        # Scrollbar for treeview
        tree_scroll = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.status_tree.yview)
        self.status_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.status_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_analytics_tab(self):
        """Create analytics tab with charts"""
        analytics_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(analytics_frame, text="Analytics")
        
        # Create matplotlib figure
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(10, 8))
        self.fig.suptitle('Hardware Analytics Dashboard', fontsize=14, fontweight='bold')
        
        # Create canvas for matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, analytics_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def create_details_tab(self):
        """Create detailed information tab"""
        details_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(details_frame, text="Detailed Report")
        
        self.details_text = scrolledtext.ScrolledText(details_frame, 
                                                     font=('Courier', 9), 
                                                     wrap=tk.WORD)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
    def create_predictions_tab(self):
        """Create predictions and lifespan tab"""
        pred_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(pred_frame, text="Predictions & Lifespan")
        
        # Predictions section
        pred_info_frame = ttk.LabelFrame(pred_frame, text="Component Lifespan Predictions", padding="10")
        pred_info_frame.pack(fill=tk.BOTH, expand=True)
        
        self.predictions_tree = ttk.Treeview(pred_info_frame, 
                                           columns=('Current_Age', 'Est_Lifespan', 'Remaining', 'Risk_Level'), 
                                           show='tree headings', height=15)
        
        self.predictions_tree.heading('#0', text='Component')
        self.predictions_tree.heading('Current_Age', text='Current Age')
        self.predictions_tree.heading('Est_Lifespan', text='Est. Lifespan')
        self.predictions_tree.heading('Remaining', text='Remaining Life')
        self.predictions_tree.heading('Risk_Level', text='Failure Risk')
        
        self.predictions_tree.column('#0', width=150)
        self.predictions_tree.column('Current_Age', width=100)
        self.predictions_tree.column('Est_Lifespan', width=100)
        self.predictions_tree.column('Remaining', width=120)
        self.predictions_tree.column('Risk_Level', width=100)
        
        pred_scroll = ttk.Scrollbar(pred_info_frame, orient=tk.VERTICAL, 
                                   command=self.predictions_tree.yview)
        self.predictions_tree.configure(yscrollcommand=pred_scroll.set)
        
        self.predictions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pred_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
    def style_widgets(self):
        """Apply custom styling"""
        style = ttk.Style()
        
        # Configure styles
        style.configure("Accent.TButton", 
                       background="#4CAF50",
                       foreground="white",
                       font=('Arial', 10, 'bold'))
        
    def start_scan(self):
        """Start the diagnostic scan in a separate thread"""
        self.scan_button.config(state='disabled', text='Scanning...')
        self.progress['value'] = 0
        self.status_label.config(text="Initializing scan...")
        
        # Clear previous data
        self.diagnostic_data = {}
        self.health_scores = {}
        self.predictions = {}
        
        # Start scan thread
        scan_thread = threading.Thread(target=self.run_diagnostics)
        scan_thread.daemon = True
        scan_thread.start()
        
    def run_diagnostics(self):
        """Run all diagnostic tests"""
        try:
            total_steps = sum(1 for var in self.check_vars.values() if var.get()) + 2
            current_step = 0
            
            # System info
            self.update_status("Collecting system information...")
            self.get_system_info()
            current_step += 1
            self.update_progress((current_step / total_steps) * 100)
            
            # Battery health
            if self.check_vars['battery'].get():
                self.update_status("Checking battery health...")
                self.check_battery_health()
                current_step += 1
                self.update_progress((current_step / total_steps) * 100)
            
            # Memory analysis
            if self.check_vars['memory'].get():
                self.update_status("Analyzing memory...")
                self.check_memory_health()
                current_step += 1
                self.update_progress((current_step / total_steps) * 100)
            
            # Storage health
            if self.check_vars['storage'].get():
                self.update_status("Checking storage health...")
                self.check_storage_health()
                current_step += 1
                self.update_progress((current_step / total_steps) * 100)
            
            # Temperature monitoring
            if self.check_vars['temperature'].get():
                self.update_status("Monitoring temperatures...")
                self.check_temperatures()
                current_step += 1
                self.update_progress((current_step / total_steps) * 100)
            
            # Performance analysis
            if self.check_vars['performance'].get():
                self.update_status("Analyzing performance...")
                self.check_performance()
                current_step += 1
                self.update_progress((current_step / total_steps) * 100)
            
            # Generate predictions
            self.update_status("Generating predictions...")
            self.generate_predictions()
            current_step += 1
            self.update_progress(100)
            
            # Update GUI
            self.update_status("Updating displays...")
            self.update_all_displays()
            
            self.update_status("Scan completed successfully!")
            
        except Exception as e:
            self.update_status(f"Error during scan: {str(e)}")
        finally:
            self.root.after(0, lambda: self.scan_button.config(state='normal', text='Start Full Scan'))
    
    def update_status(self, message):
        """Update status label safely from thread"""
        self.root.after(0, lambda: self.status_label.config(text=message))
    
    def update_progress(self, value):
        """Update progress bar safely from thread"""
        self.root.after(0, lambda: setattr(self.progress, 'value', value))
    
    def get_system_info(self):
        """Get system information"""
        self.diagnostic_data['system'] = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'hostname': platform.node(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
            'uptime_hours': (time.time() - psutil.boot_time()) / 3600
        }
    
    def check_battery_health(self):
        """Check battery health and predict lifespan"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                # Calculate health based on capacity and cycles (estimated)
                charge_percent = battery.percent
                is_plugged = battery.power_plugged
                
                # Estimate battery age based on system uptime and usage patterns
                uptime_days = (time.time() - psutil.boot_time()) / (24 * 3600)
                estimated_cycles = max(1, uptime_days / 2)  # Rough estimate
                
                # Battery health calculation (simplified model)
                health_score = max(0, min(100, 100 - (estimated_cycles / 10)))
                
                # Predict remaining lifespan
                typical_lifespan_cycles = 500  # Typical laptop battery
                remaining_cycles = max(0, typical_lifespan_cycles - estimated_cycles)
                remaining_years = remaining_cycles / (365 / 2)  # Assuming charge every 2 days
                
                self.diagnostic_data['battery'] = {
                    'present': True,
                    'percent': charge_percent,
                    'plugged': is_plugged,
                    'estimated_cycles': int(estimated_cycles),
                    'health_score': round(health_score, 1),
                    'remaining_cycles': int(remaining_cycles),
                    'estimated_remaining_years': round(remaining_years, 1),
                    'secsleft': getattr(battery, 'secsleft', None)
                }
                
                self.health_scores['battery'] = health_score
                
            else:
                self.diagnostic_data['battery'] = {'present': False}
                self.health_scores['battery'] = 100  # Desktop PC
                
        except Exception as e:
            self.diagnostic_data['battery'] = {'error': str(e)}
            self.health_scores['battery'] = 50
    
    def check_memory_health(self):
        """Check memory health and predict failures"""
        try:
            memory = psutil.virtual_memory()
            
            # Memory health factors
            usage_percent = memory.percent
            available_gb = memory.available / (1024**3)
            total_gb = memory.total / (1024**3)
            
            # Health score based on usage patterns and availability
            if usage_percent > 90:
                health_score = 30
            elif usage_percent > 80:
                health_score = 60
            elif usage_percent > 70:
                health_score = 80
            else:
                health_score = 95
            
            # Estimate RAM age (simplified)
            # Assume newer systems have more RAM
            if total_gb >= 16:
                estimated_age_years = 2
            elif total_gb >= 8:
                estimated_age_years = 4
            else:
                estimated_age_years = 6
            
            # RAM typically lasts 8-10 years
            typical_lifespan = 10
            remaining_years = max(0, typical_lifespan - estimated_age_years)
            
            self.diagnostic_data['memory'] = {
                'total_gb': round(total_gb, 2),
                'available_gb': round(available_gb, 2),
                'used_percent': usage_percent,
                'health_score': health_score,
                'estimated_age_years': estimated_age_years,
                'estimated_remaining_years': remaining_years
            }
            
            self.health_scores['memory'] = health_score
            
        except Exception as e:
            self.diagnostic_data['memory'] = {'error': str(e)}
            self.health_scores['memory'] = 50
    
    def check_storage_health(self):
        """Check storage health and predict failures"""
        try:
            storage_data = {}
            partitions = psutil.disk_partitions()
            
            total_health = []
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # Calculate health based on usage
                    used_percent = (usage.used / usage.total) * 100
                    
                    if used_percent > 95:
                        health_score = 20
                    elif used_percent > 85:
                        health_score = 50
                    elif used_percent > 70:
                        health_score = 75
                    else:
                        health_score = 90
                    
                    # Estimate drive age based on size (rough approximation)
                    size_gb = usage.total / (1024**3)
                    if size_gb > 1000:  # > 1TB
                        estimated_age = 2
                        typical_lifespan = 8 if 'SSD' in partition.fstype.upper() else 5
                    else:
                        estimated_age = 4
                        typical_lifespan = 10 if 'SSD' in partition.fstype.upper() else 6
                    
                    remaining_years = max(0, typical_lifespan - estimated_age)
                    
                    storage_data[partition.device] = {
                        'mountpoint': partition.mountpoint,
                        'filesystem': partition.fstype,
                        'total_gb': round(size_gb, 2),
                        'used_percent': round(used_percent, 2),
                        'health_score': health_score,
                        'estimated_age_years': estimated_age,
                        'estimated_remaining_years': remaining_years,
                        'drive_type': 'SSD' if 'nvme' in partition.device.lower() else 'HDD'
                    }
                    
                    total_health.append(health_score)
                    
                except PermissionError:
                    continue
            
            self.diagnostic_data['storage'] = storage_data
            self.health_scores['storage'] = sum(total_health) / len(total_health) if total_health else 50
            
        except Exception as e:
            self.diagnostic_data['storage'] = {'error': str(e)}
            self.health_scores['storage'] = 50
    
    def check_temperatures(self):
        """Check system temperatures"""
        try:
            temps = psutil.sensors_temperatures()
            temp_data = {}
            health_scores = []
            
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        current_temp = entry.current
                        
                        # Health based on temperature
                        if current_temp > 80:
                            health_score = 20
                        elif current_temp > 70:
                            health_score = 50
                        elif current_temp > 60:
                            health_score = 75
                        else:
                            health_score = 95
                        
                        temp_data[f"{name}_{entry.label}"] = {
                            'current': current_temp,
                            'high': entry.high,
                            'critical': entry.critical,
                            'health_score': health_score
                        }
                        health_scores.append(health_score)
            
            self.diagnostic_data['temperature'] = temp_data
            self.health_scores['temperature'] = sum(health_scores) / len(health_scores) if health_scores else 85
            
        except Exception as e:
            self.diagnostic_data['temperature'] = {'error': str(e)}
            self.health_scores['temperature'] = 85
    
    def check_performance(self):
        """Check overall system performance"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            
            # Performance health
            if cpu_percent > 90:
                perf_health = 30
            elif cpu_percent > 70:
                perf_health = 60
            else:
                perf_health = 90
            
            self.diagnostic_data['performance'] = {
                'cpu_usage': cpu_percent,
                'cpu_frequency': cpu_freq.current if cpu_freq else None,
                'cpu_cores': psutil.cpu_count(),
                'health_score': perf_health
            }
            
            self.health_scores['performance'] = perf_health
            
        except Exception as e:
            self.diagnostic_data['performance'] = {'error': str(e)}
            self.health_scores['performance'] = 70
    
    def generate_predictions(self):
        """Generate failure predictions and lifespan estimates"""
        self.predictions = {}
        
        # Battery predictions
        if 'battery' in self.diagnostic_data and self.diagnostic_data['battery'].get('present'):
            battery_data = self.diagnostic_data['battery']
            health = battery_data.get('health_score', 50)
            
            if health < 30:
                risk_level = "HIGH"
                time_to_failure = "3-6 months"
            elif health < 60:
                risk_level = "MEDIUM"
                time_to_failure = "6-12 months"
            else:
                risk_level = "LOW"
                time_to_failure = f"{battery_data.get('estimated_remaining_years', 1):.1f} years"
            
            self.predictions['Battery'] = {
                'current_age': f"{battery_data.get('estimated_cycles', 0)} cycles",
                'estimated_lifespan': "500-1000 cycles",
                'remaining_life': time_to_failure,
                'risk_level': risk_level
            }
        
        # Memory predictions
        if 'memory' in self.diagnostic_data:
            mem_data = self.diagnostic_data['memory']
            age = mem_data.get('estimated_age_years', 0)
            remaining = mem_data.get('estimated_remaining_years', 0)
            
            if remaining < 1:
                risk_level = "HIGH"
            elif remaining < 3:
                risk_level = "MEDIUM"  
            else:
                risk_level = "LOW"
            
            self.predictions['Memory (RAM)'] = {
                'current_age': f"{age} years",
                'estimated_lifespan': "8-10 years",
                'remaining_life': f"{remaining:.1f} years",
                'risk_level': risk_level
            }
        
        # Storage predictions
        if 'storage' in self.diagnostic_data:
            for device, storage_data in self.diagnostic_data['storage'].items():
                if isinstance(storage_data, dict) and 'health_score' in storage_data:
                    age = storage_data.get('estimated_age_years', 0)
                    remaining = storage_data.get('estimated_remaining_years', 0)
                    drive_type = storage_data.get('drive_type', 'HDD')
                    
                    if remaining < 1:
                        risk_level = "HIGH"
                    elif remaining < 2:
                        risk_level = "MEDIUM"
                    else:
                        risk_level = "LOW"
                    
                    self.predictions[f'Storage ({device})'] = {
                        'current_age': f"{age} years",
                        'estimated_lifespan': f"{'8-10' if drive_type == 'SSD' else '5-7'} years",
                        'remaining_life': f"{remaining:.1f} years",
                        'risk_level': risk_level
                    }
    
    def update_all_displays(self):
        """Update all GUI displays with diagnostic data"""
        self.root.after(0, self.update_overview)
        self.root.after(0, self.update_analytics)
        self.root.after(0, self.update_details)
        self.root.after(0, self.update_predictions)
        self.root.after(0, self.update_health_summary)
    
    def update_overview(self):
        """Update overview tab"""
        # System info
        sys_info = self.diagnostic_data.get('system', {})
        info_text = f"""Platform: {sys_info.get('platform', 'Unknown')}
Version: {sys_info.get('platform_version', 'Unknown')}
Architecture: {sys_info.get('architecture', 'Unknown')}
Processor: {sys_info.get('processor', 'Unknown')}
Hostname: {sys_info.get('hostname', 'Unknown')}
Boot Time: {sys_info.get('boot_time', 'Unknown')}
Uptime: {sys_info.get('uptime_hours', 0):.1f} hours"""
        
        self.sys_info_text.delete(1.0, tk.END)
        self.sys_info_text.insert(1.0, info_text)
        
        # Component status tree
        for item in self.status_tree.get_children():
            self.status_tree.delete(item)
        
        for component, health_score in self.health_scores.items():
            if health_score >= 80:
                status = "GOOD"
                status_color = "green"
            elif health_score >= 60:
                status = "FAIR"
                status_color = "orange"
            else:
                status = "POOR"
                status_color = "red"
            
            details = self.get_component_details(component)
            
            item = self.status_tree.insert('', 'end', text=component.title(), 
                                         values=(f"{health_score:.1f}%", status, details))
            
            if status == "POOR":
                self.status_tree.set(item, 'Status', f"⚠ {status}")
            elif status == "FAIR":
                self.status_tree.set(item, 'Status', f"⚠ {status}")
            else:
                self.status_tree.set(item, 'Status', f"✓ {status}")
    
    def get_component_details(self, component):
        """Get summary details for component"""
        data = self.diagnostic_data.get(component, {})
        
        if component == 'battery':
            if data.get('present'):
                return f"{data.get('percent', 0):.0f}% charge, ~{data.get('estimated_remaining_years', 0):.1f}y left"
            else:
                return "No battery detected (Desktop PC)"
        elif component == 'memory':
            return f"{data.get('used_percent', 0):.0f}% used, {data.get('available_gb', 0):.1f}GB free"
        elif component == 'storage':
            if isinstance(data, dict) and data:
                first_drive = next(iter(data.values()))
                if isinstance(first_drive, dict):
                    return f"{first_drive.get('used_percent', 0):.0f}% used"
            return "Multiple drives detected"
        elif component == 'temperature':
            if isinstance(data, dict) and data:
                temps = [entry.get('current', 0) for entry in data.values() if isinstance(entry, dict)]
                avg_temp = sum(temps) / len(temps) if temps else 0
                return f"Avg: {avg_temp:.0f}°C"
            return "Temperature monitoring available"
        elif component == 'performance':
            return f"CPU: {data.get('cpu_usage', 0):.0f}% usage"
        
        return "Data available"
    
    def update_analytics(self):
        """Update analytics charts"""
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.clear()
        
        components = list(self.health_scores.keys())
        scores = list(self.health_scores.values())
        colors = ['red' if s < 60 else 'orange' if s < 80 else 'green' for s in scores]
        
        self.ax1.bar(components, scores, color=colors)
        self.ax1.set_title('Component Health Scores')
        self.ax1.set_ylabel('Health Score (%)')
        self.ax1.set_ylim(0, 100)
        self.ax1.tick_params(axis='x', rotation=45)
        
        if 'memory' in self.diagnostic_data:
            mem_data = self.diagnostic_data['memory']
            used = mem_data.get('used_percent', 0)
            free = 100 - used
            
            self.ax2.pie([used, free], labels=['Used', 'Free'], autopct='%1.1f%%',
                        colors=['red' if used > 80 else 'orange' if used > 70 else 'lightblue', 'lightgreen'])
            self.ax2.set_title('Memory Usage')
        
        if 'storage' in self.diagnostic_data:
            storage_data = self.diagnostic_data['storage']
            devices = []
            usage_pcts = []
            
            for device, data in storage_data.items():
                if isinstance(data, dict) and 'used_percent' in data:
                    devices.append(device.replace('\\', ''))
                    usage_pcts.append(data['used_percent'])
            
            if devices:
                colors = ['red' if u > 85 else 'orange' if u > 70 else 'lightblue' for u in usage_pcts]
                self.ax3.barh(devices, usage_pcts, color=colors)
                self.ax3.set_title('Storage Usage by Drive')
                self.ax3.set_xlabel('Usage (%)')
                self.ax3.set_xlim(0, 100)
        
        if 'temperature' in self.diagnostic_data:
            temp_data = self.diagnostic_data['temperature']
            if temp_data and not temp_data.get('error'):
                temp_names = []
                temp_values = []
                
                for name, data in temp_data.items():
                    if isinstance(data, dict) and 'current' in data:
                        temp_names.append(name.split('_')[-1])
                        temp_values.append(data['current'])
                
                if temp_names:
                    colors = ['red' if t > 80 else 'orange' if t > 70 else 'lightblue' for t in temp_values]
                    self.ax4.bar(temp_names, temp_values, color=colors)
                    self.ax4.set_title('Temperature Sensors')
                    self.ax4.set_ylabel('Temperature (°C)')
                    self.ax4.tick_params(axis='x', rotation=45)
                    
                    self.ax4.axhline(y=70, color='orange', linestyle='--', alpha=0.5, label='Warning')
                    self.ax4.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='Critical')
                    self.ax4.legend()
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def update_details(self):
        """Update detailed report tab"""
        report = "="*60 + "\n"
        report += "DETAILED HARDWARE DIAGNOSTIC REPORT\n"
        report += "="*60 + "\n\n"
        
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if 'system' in self.diagnostic_data:
            sys_data = self.diagnostic_data['system']
            report += "SYSTEM INFORMATION:\n"
            report += "-" * 30 + "\n"
            for key, value in sys_data.items():
                report += f"{key.replace('_', ' ').title()}: {value}\n"
            report += "\n"
        
        if 'battery' in self.diagnostic_data:
            battery_data = self.diagnostic_data['battery']
            report += "BATTERY ANALYSIS:\n"
            report += "-" * 30 + "\n"
            if battery_data.get('present'):
                report += f"Current Charge: {battery_data.get('percent', 0):.1f}%\n"
                report += f"Power Plugged: {'Yes' if battery_data.get('plugged') else 'No'}\n"
                report += f"Estimated Cycles: {battery_data.get('estimated_cycles', 0)}\n"
                report += f"Health Score: {battery_data.get('health_score', 0):.1f}%\n"
                report += f"Estimated Remaining Years: {battery_data.get('estimated_remaining_years', 0):.1f}\n"
                
                if battery_data.get('secsleft'):
                    hours = battery_data['secsleft'] // 3600
                    minutes = (battery_data['secsleft'] % 3600) // 60
                    report += f"Time Remaining: {hours}h {minutes}m\n"
            else:
                report += "No battery detected (Desktop system)\n"
            report += "\n"
        
        if 'memory' in self.diagnostic_data:
            mem_data = self.diagnostic_data['memory']
            report += "MEMORY ANALYSIS:\n"
            report += "-" * 30 + "\n"
            report += f"Total RAM: {mem_data.get('total_gb', 0):.2f} GB\n"
            report += f"Available RAM: {mem_data.get('available_gb', 0):.2f} GB\n"
            report += f"Used Percentage: {mem_data.get('used_percent', 0):.1f}%\n"
            report += f"Health Score: {mem_data.get('health_score', 0):.1f}%\n"
            report += f"Estimated Age: {mem_data.get('estimated_age_years', 0)} years\n"
            report += f"Estimated Remaining Life: {mem_data.get('estimated_remaining_years', 0):.1f} years\n"
            report += "\n"
        
        if 'storage' in self.diagnostic_data:
            storage_data = self.diagnostic_data['storage']
            report += "STORAGE ANALYSIS:\n"
            report += "-" * 30 + "\n"
            for device, data in storage_data.items():
                if isinstance(data, dict) and 'total_gb' in data:
                    report += f"Device: {device}\n"
                    report += f"  Mount Point: {data.get('mountpoint', 'N/A')}\n"
                    report += f"  File System: {data.get('filesystem', 'N/A')}\n"
                    report += f"  Total Size: {data.get('total_gb', 0):.2f} GB\n"
                    report += f"  Used: {data.get('used_percent', 0):.1f}%\n"
                    report += f"  Drive Type: {data.get('drive_type', 'Unknown')}\n"
                    report += f"  Health Score: {data.get('health_score', 0):.1f}%\n"
                    report += f"  Estimated Age: {data.get('estimated_age_years', 0)} years\n"
                    report += f"  Est. Remaining Life: {data.get('estimated_remaining_years', 0):.1f} years\n"
                    report += "\n"
        
        if 'temperature' in self.diagnostic_data:
            temp_data = self.diagnostic_data['temperature']
            report += "TEMPERATURE MONITORING:\n"
            report += "-" * 30 + "\n"
            if temp_data and not temp_data.get('error'):
                for sensor, data in temp_data.items():
                    if isinstance(data, dict):
                        report += f"Sensor: {sensor}\n"
                        report += f"  Current: {data.get('current', 0):.1f}°C\n"
                        if data.get('high'):
                            report += f"  High Threshold: {data['high']:.1f}°C\n"
                        if data.get('critical'):
                            report += f"  Critical Threshold: {data['critical']:.1f}°C\n"
                        report += f"  Health Score: {data.get('health_score', 0):.1f}%\n"
                        report += "\n"
            else:
                report += "Temperature sensors not available or accessible\n\n"
        
        if 'performance' in self.diagnostic_data:
            perf_data = self.diagnostic_data['performance']
            report += "PERFORMANCE ANALYSIS:\n"
            report += "-" * 30 + "\n"
            report += f"CPU Usage: {perf_data.get('cpu_usage', 0):.1f}%\n"
            if perf_data.get('cpu_frequency'):
                report += f"CPU Frequency: {perf_data['cpu_frequency']:.0f} MHz\n"
            report += f"CPU Cores: {perf_data.get('cpu_cores', 0)}\n"
            report += f"Performance Health Score: {perf_data.get('health_score', 0):.1f}%\n"
            report += "\n"
        
        report += "OVERALL ASSESSMENT:\n"
        report += "-" * 30 + "\n"
        
        if self.health_scores:
            overall_health = sum(self.health_scores.values()) / len(self.health_scores)
            report += f"Overall System Health: {overall_health:.1f}%\n"
            
            if overall_health >= 85:
                report += "Status: EXCELLENT - System is running optimally\n"
            elif overall_health >= 70:
                report += "Status: GOOD - System is healthy with minor issues\n"
            elif overall_health >= 50:
                report += "Status: FAIR - Some components need attention\n"
            else:
                report += "Status: POOR - Multiple components require immediate attention\n"
            
            report += "\nRecommendations:\n"
            
            for component, health in self.health_scores.items():
                if health < 60:
                    if component == 'battery':
                        report += f"• Battery: Consider replacement, health at {health:.1f}%\n"
                    elif component == 'memory':
                        report += f"• Memory: High usage detected, consider adding RAM\n"
                    elif component == 'storage':
                        report += f"• Storage: Check disk space and consider cleanup/upgrade\n"
                    elif component == 'temperature':
                        report += f"• Temperature: Check cooling system, clean fans/vents\n"
                    elif component == 'performance':
                        report += f"• Performance: High CPU usage, check for resource-heavy processes\n"
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, report)
    
    def update_predictions(self):
        """Update predictions tab"""
        for item in self.predictions_tree.get_children():
            self.predictions_tree.delete(item)
        
        for component, pred_data in self.predictions.items():
            if pred_data['risk_level'] == 'HIGH':
                risk_symbol = "🔴 HIGH"
            elif pred_data['risk_level'] == 'MEDIUM':
                risk_symbol = "🟡 MEDIUM"
            else:
                risk_symbol = "🟢 LOW"
            
            self.predictions_tree.insert('', 'end', text=component,
                                       values=(pred_data['current_age'],
                                              pred_data['estimated_lifespan'],
                                              pred_data['remaining_life'],
                                              risk_symbol))
    
    def update_health_summary(self):
        """Update health summary in control panel"""
        summary = "HEALTH SUMMARY\n" + "="*20 + "\n\n"
        
        if self.health_scores:
            overall_health = sum(self.health_scores.values()) / len(self.health_scores)
            
            if overall_health >= 85:
                status_emoji = "🟢"
                status_text = "EXCELLENT"
            elif overall_health >= 70:
                status_emoji = "🟡"
                status_text = "GOOD"
            elif overall_health >= 50:
                status_emoji = "🟠"
                status_text = "FAIR"
            else:
                status_emoji = "🔴"
                status_text = "POOR"
            
            summary += f"Overall: {status_emoji} {status_text}\n"
            summary += f"Score: {overall_health:.1f}%\n\n"
            
            for component, health in sorted(self.health_scores.items()):
                if health >= 80:
                    emoji = "🟢"
                elif health >= 60:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                
                summary += f"{emoji} {component.title()}: {health:.0f}%\n"
            
            high_risk = sum(1 for pred in self.predictions.values() 
                          if pred.get('risk_level') == 'HIGH')
            if high_risk > 0:
                summary += f"\n⚠️  {high_risk} component(s) at high failure risk"
        
        self.health_text.delete(1.0, tk.END)
        self.health_text.insert(1.0, summary)

def install_dependencies():
    """Check and install required dependencies"""
    required_packages = ['psutil', 'matplotlib']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Installing required packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install packages: {', '.join(missing_packages)}")
            print("Please install manually: pip install " + " ".join(missing_packages))
            return False
    return True

def main():
    """Main function to run the application"""
    print("Advanced PC Hardware Diagnostic Tool with GUI")
    print("Checking dependencies...")
    
    if not install_dependencies():
        print("Cannot start application without required dependencies.")
        return
    
    try:
        root = tk.Tk()
        app = AdvancedDiagnosticGUI(root)
        
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        print("Starting GUI application...")
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        try:
            messagebox.showerror("Error", f"Failed to start application: {e}")
        except Exception:
            pass

if __name__ == "__main__":
    main()
