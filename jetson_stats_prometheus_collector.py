#!/usr/bin/python3
# -*- coding: utf-8 -*-

import atexit
import argparse
from jtop import jtop, JtopException
from prometheus_client.core import InfoMetricFamily, GaugeMetricFamily, REGISTRY
from prometheus_client import make_wsgi_app
from wsgiref.simple_server import make_server

class JetsonStatsCollector(object):
    def __init__(self):
        atexit.register(self.cleanup)
        self._jetson = jtop()
        self._jetson.start()
        print("✅ Jetson-stats connection established")

    def cleanup(self):
        print("Closing jetson-stats connection...")
        self._jetson.close()

    def extract_value(self, data):
        """Extract a single numeric value from various data types"""
        if isinstance(data, list):
            if len(data) > 0:
                return float(data[0])
            return 0.0
        elif isinstance(data, (int, float)):
            return float(data)
        elif isinstance(data, dict):
            # Try common keys
            for key in ['val', 'value', 'cur', 'current', 'avg', 'speed']:
                if key in data:
                    return self.extract_value(data[key])
        return 0.0

    def collect(self):
        if self._jetson.ok():
            # Board info - handle different structures
            try:
                board_info = {}
                if hasattr(self._jetson, 'board') and self._jetson.board:
                    board = self._jetson.board
                    
                    # Try to get machine/platform info
                    if 'info' in board:
                        board_info['machine'] = str(board['info'].get('machine', 'unknown'))
                        board_info['jetpack'] = str(board['info'].get('jetpack', 'unknown'))
                        board_info['l4t'] = str(board['info'].get('L4T', 'unknown'))
                    elif 'platform' in board:
                        board_info['machine'] = str(board['platform'].get('Machine', 'unknown'))
                        board_info['jetpack'] = str(board.get('Jetpack', 'unknown'))
                        board_info['l4t'] = str(board.get('L4T', 'unknown'))
                    
                    # Try to get hardware info
                    if 'hardware' in board:
                        board_info['type'] = str(board['hardware'].get('TYPE', 'unknown'))
                        board_info['codename'] = str(board['hardware'].get('CODENAME', 'unknown'))
                        board_info['soc'] = str(board['hardware'].get('SOC', 'unknown'))
                    
                    if board_info:
                        i = InfoMetricFamily('jetson_info', 'Jetson board information')
                        i.add_metric([], board_info)
                        yield i
            except Exception as e:
                print(f"Warning: Could not collect board info: {e}")

            # CPU usage
            try:
                if hasattr(self._jetson, 'cpu') and self._jetson.cpu:
                    g = GaugeMetricFamily('jetson_usage_cpu', 'CPU % usage', labels=['cpu'])
                    for cpu_name, cpu_data in self._jetson.cpu.items():
                        try:
                            value = self.extract_value(cpu_data)
                            g.add_metric([cpu_name.lower()], value)
                        except:
                            pass
                    yield g
            except Exception as e:
                print(f"Warning: Could not collect CPU info: {e}")

            # GPU usage
            try:
                if hasattr(self._jetson, 'gpu') and self._jetson.gpu:
                    gpu_val = self.extract_value(self._jetson.gpu)
                    
                    # GPU usage percentage
                    g = GaugeMetricFamily('jetson_usage_gpu', 'GPU % usage')
                    g.add_metric([], gpu_val)
                    yield g
                    
                    # GPU frequency
                    if isinstance(self._jetson.gpu, dict) and 'frq' in self._jetson.gpu:
                        gpu_freq = self.extract_value(self._jetson.gpu['frq'])
                        if gpu_freq > 0:
                            g = GaugeMetricFamily('jetson_freq_gpu', 'GPU frequency MHz')
                            g.add_metric([], gpu_freq)
                            yield g
            except Exception as e:
                print(f"Warning: Could not collect GPU info: {e}")

            # Memory usage
            try:
                if hasattr(self._jetson, 'memory') and self._jetson.memory:
                    mem = self._jetson.memory
                    
                    # RAM
                    if 'RAM' in mem:
                        g = GaugeMetricFamily('jetson_usage_ram', 'RAM usage MB', labels=['type'])
                        ram = mem['RAM']
                        if isinstance(ram, dict):
                            used = self.extract_value(ram.get('used', 0))
                            total = self.extract_value(ram.get('tot', ram.get('total', 0)))
                            g.add_metric(['used'], used)
                            g.add_metric(['total'], total)
                        yield g
                    
                    # SWAP
                    if 'SWAP' in mem:
                        g = GaugeMetricFamily('jetson_usage_swap', 'SWAP usage MB', labels=['type'])
                        swap = mem['SWAP']
                        if isinstance(swap, dict):
                            used = self.extract_value(swap.get('used', 0))
                            total = self.extract_value(swap.get('tot', swap.get('total', 0)))
                            g.add_metric(['used'], used)
                            g.add_metric(['total'], total)
                        yield g
            except Exception as e:
                print(f"Warning: Could not collect memory info: {e}")

            # Temperature sensors
            try:
                if hasattr(self._jetson, 'temperature') and self._jetson.temperature:
                    g = GaugeMetricFamily('jetson_temperatures', 'Temperature sensors Celsius', labels=['sensor'])
                    for sensor_name, temp_value in self._jetson.temperature.items():
                        try:
                            temp = self.extract_value(temp_value)
                            g.add_metric([sensor_name.lower()], temp)
                        except:
                            pass
                    yield g
            except Exception as e:
                print(f"Warning: Could not collect temperature info: {e}")

            # Power consumption
            try:
                if hasattr(self._jetson, 'power') and self._jetson.power:
                    g = GaugeMetricFamily('jetson_power', 'Power consumption mW', labels=['rail'])
                    
                    if isinstance(self._jetson.power, dict):
                        for rail_name, power_data in self._jetson.power.items():
                            try:
                                power_val = self.extract_value(power_data)
                                if power_val > 0:
                                    g.add_metric([rail_name.lower()], power_val)
                            except:
                                pass
                        yield g
                    else:
                        power_val = self.extract_value(self._jetson.power)
                        g.add_metric(['total'], power_val)
                        yield g
            except Exception as e:
                print(f"Warning: Could not collect power info: {e}")

            # Fan speed
            try:
                if hasattr(self._jetson, 'fan') and self._jetson.fan:
                    g = GaugeMetricFamily('jetson_fan_speed', 'Fan speed %', labels=['fan'])
                    for fan_name, fan_data in self._jetson.fan.items():
                        try:
                            speed = self.extract_value(fan_data)
                            g.add_metric([fan_name.lower()], speed)
                        except Exception as fan_err:
                            print(f"Warning: Could not process fan '{fan_name}': {fan_err}")
                    yield g
            except Exception as e:
                print(f"Warning: Could not collect fan info: {e}")

            # Disk usage
            try:
                if hasattr(self._jetson, 'disk') and self._jetson.disk:
                    g = GaugeMetricFamily('jetson_disk_usage', 'Disk usage MB', labels=['type'])
                    disk = self._jetson.disk
                    if isinstance(disk, dict):
                        used = self.extract_value(disk.get('used', 0))
                        total = self.extract_value(disk.get('total', disk.get('tot', 0)))
                        g.add_metric(['used'], used)
                        g.add_metric(['total'], total)
                        yield g
            except Exception as e:
                print(f"Warning: Could not collect disk info: {e}")

            # Stats (uptime, etc.)
            try:
                if hasattr(self._jetson, 'stats') and self._jetson.stats:
                    stats = self._jetson.stats
                    
                    # Uptime
                    if 'uptime' in stats:
                        g = GaugeMetricFamily('jetson_uptime_seconds', 'System uptime in seconds')
                        uptime_val = stats['uptime']
                        if hasattr(uptime_val, 'total_seconds'):
                            g.add_metric([], uptime_val.total_seconds())
                        else:
                            uptime_seconds = self.extract_value(uptime_val)
                            g.add_metric([], uptime_seconds)
                        yield g
            except Exception as e:
                print(f"Warning: Could not collect stats info: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Jetson Stats Prometheus Collector')
    parser.add_argument('--port', type=int, default=8000, help='Port to listen on (default: 8000)')
    args = parser.parse_args()

    try:
        print(f"Starting Jetson Stats Prometheus Collector on port {args.port}...")
        
        # First, test if we can create the collector
        collector = JetsonStatsCollector()
        print("Testing metric collection...")
        
        # Try to collect once to verify it works
        test_metrics = list(collector.collect())
        print(f"✅ Successfully collected {len(test_metrics)} metric families")
        
        # Register and start server
        REGISTRY.register(collector)
        app = make_wsgi_app()
        httpd = make_server('0.0.0.0', args.port, app)
        print(f"✅ Collector running on http://0.0.0.0:{args.port}/metrics")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except JtopException as e:
        print(f"❌ JTop Error: {e}")
        print("Make sure jetson-stats is properly installed and you've rebooted after installation")
        print("Try running: sudo systemctl restart jtop.service")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()