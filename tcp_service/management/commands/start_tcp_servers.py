"""
Django Management Command to Start TCP Servers

Starts JT808 and JT1078 TCP servers for dashcam communication.
Run with: python manage.py start_tcp_servers
"""
import asyncio
import signal
import logging
import os
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start JT808/JT1078 TCP servers for dashcam communication'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--jt808-host',
            default='0.0.0.0',
            help='JT808 server host (default: 0.0.0.0)'
        )
        parser.add_argument(
            '--jt808-port',
            type=int,
            default=int(os.environ.get('JT808_PORT', 6665)),
            help='JT808 server port (default: 6665)'
        )
        parser.add_argument(
            '--jt1078-host',
            default='0.0.0.0',
            help='JT1078 server host (default: 0.0.0.0)'
        )
        parser.add_argument(
            '--jt1078-port',
            type=int,
            default=int(os.environ.get('JT1078_PORT', 6664)),
            help='JT1078 server port (default: 6664)'
        )
        parser.add_argument(
            '--jt808-only',
            action='store_true',
            help='Start only JT808 server (no video)'
        )
        parser.add_argument(
            '--jt1078-only',
            action='store_true',
            help='Start only JT1078 server (video only)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting TCP servers...'))
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        
        # Run the servers
        try:
            asyncio.run(self._run_servers(options))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nShutting down servers...'))
    
    async def _run_servers(self, options):
        """Run TCP servers asynchronously."""
        from tcp_service.tcp.device_manager import DeviceManager
        from tcp_service.tcp.jt808_server import JT808Server
        from tcp_service.tcp.jt1078_server import JT1078Server
        
        # Shared device manager
        device_manager = DeviceManager()
        
        # Setup servers
        servers = []
        tasks = []
        
        if not options['jt1078_only']:
            jt808_server = JT808Server(
                host=options['jt808_host'],
                port=options['jt808_port'],
                device_manager=device_manager
            )
            servers.append(jt808_server)
            self.stdout.write(
                f"JT808 server will listen on {options['jt808_host']}:{options['jt808_port']}"
            )
        
        if not options['jt808_only']:
            jt1078_server = JT1078Server(
                host=options['jt1078_host'],
                port=options['jt1078_port'],
                device_manager=device_manager
            )
            servers.append(jt1078_server)
            self.stdout.write(
                f"JT1078 server will listen on {options['jt1078_host']}:{options['jt1078_port']}"
            )
        
        if not servers:
            self.stdout.write(self.style.ERROR('No servers to start!'))
            return
        
        # Setup signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        shutdown_event = asyncio.Event()
        
        def signal_handler():
            self.stdout.write(self.style.WARNING('\nReceived shutdown signal'))
            shutdown_event.set()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                pass
        
        # Start servers
        for server in servers:
            tasks.append(asyncio.create_task(server.start()))
        
        self.stdout.write(self.style.SUCCESS('TCP servers started!'))
        self.stdout.write('Press Ctrl+C to stop...\n')
        
        # Wait for shutdown
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            # Stop all servers
            for server in servers:
                await server.stop()
            
            self.stdout.write(self.style.SUCCESS('TCP servers stopped.'))
