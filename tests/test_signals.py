import asyncio
import signal
import subprocess
import sys
import time
import uvloop

from uvloop import _testbase as tb

DELAY = 0.1


class _TestSignal:
    NEW_LOOP = None

    @tb.silence_long_exec_warning()
    def test_signals_sigint_pycode_stop(self):
        async def runner():
            PROG = R"""\
import asyncio
import uvloop
import time

from uvloop import _testbase as tb

async def worker():
    print('READY', flush=True)
    time.sleep(200)

@tb.silence_long_exec_warning()
def run():
    loop = """ + self.NEW_LOOP + """
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(worker())
    finally:
        loop.close()

run()
"""

            proc = await asyncio.create_subprocess_exec(
                sys.executable, b'-c', PROG,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                loop=self.loop)

            await proc.stdout.readline()
            time.sleep(DELAY)
            proc.send_signal(signal.SIGINT)
            out, err = await proc.communicate()
            self.assertIn(b'KeyboardInterrupt', err)
            self.assertEqual(out, b'')

        self.loop.run_until_complete(runner())

    @tb.silence_long_exec_warning()
    def test_signals_sigint_pycode_continue(self):
        async def runner():
            PROG = R"""\
import asyncio
import uvloop
import time

from uvloop import _testbase as tb

async def worker():
    print('READY', flush=True)
    try:
        time.sleep(200)
    except KeyboardInterrupt:
        print("oups")
    await asyncio.sleep(0.5)
    print('done')

@tb.silence_long_exec_warning()
def run():
    loop = """ + self.NEW_LOOP + """
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(worker())
    finally:
        loop.close()

run()
"""

            proc = await asyncio.create_subprocess_exec(
                sys.executable, b'-c', PROG,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                loop=self.loop)

            await proc.stdout.readline()
            time.sleep(DELAY)
            proc.send_signal(signal.SIGINT)
            out, err = await proc.communicate()
            self.assertEqual(err, b'')
            self.assertEqual(out, b'oups\ndone\n')

        self.loop.run_until_complete(runner())

    @tb.silence_long_exec_warning()
    def test_signals_sigint_uvcode(self):
        async def runner():
            PROG = R"""\
import asyncio
import uvloop

srv = None

async def worker():
    global srv
    cb = lambda *args: None
    srv = await asyncio.start_server(cb, '127.0.0.1', 0)
    print('READY', flush=True)

loop = """ + self.NEW_LOOP + """
asyncio.set_event_loop(loop)
loop.create_task(worker())
try:
    loop.run_forever()
finally:
    srv.close()
    loop.run_until_complete(srv.wait_closed())
    loop.close()
"""

            proc = await asyncio.create_subprocess_exec(
                sys.executable, b'-c', PROG,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                loop=self.loop)

            await proc.stdout.readline()
            time.sleep(DELAY)
            proc.send_signal(signal.SIGINT)
            out, err = await proc.communicate()
            self.assertIn(b'KeyboardInterrupt', err)

        self.loop.run_until_complete(runner())

    @tb.silence_long_exec_warning()
    def test_signals_sigint_and_custom_handler(self):
        async def runner():
            PROG = R"""\
import asyncio
import signal
import uvloop

srv = None

async def worker():
    global srv
    cb = lambda *args: None
    srv = await asyncio.start_server(cb, '127.0.0.1', 0)
    print('READY', flush=True)

def handler_sig(say):
    print(say, flush=True)
    exit()

def handler_hup(say):
    print(say, flush=True)

loop = """ + self.NEW_LOOP + """
loop.add_signal_handler(signal.SIGINT, handler_sig, '!s-int!')
loop.add_signal_handler(signal.SIGHUP, handler_hup, '!s-hup!')
asyncio.set_event_loop(loop)
loop.create_task(worker())
try:
    loop.run_forever()
finally:
    srv.close()
    loop.run_until_complete(srv.wait_closed())
    loop.close()
"""

            proc = await asyncio.create_subprocess_exec(
                sys.executable, b'-c', PROG,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                loop=self.loop)

            await proc.stdout.readline()
            time.sleep(DELAY)
            proc.send_signal(signal.SIGHUP)
            time.sleep(DELAY)
            proc.send_signal(signal.SIGINT)
            out, err = await proc.communicate()
            self.assertEqual(err, b'')
            self.assertIn(b'!s-hup!', out)
            self.assertIn(b'!s-int!', out)

        self.loop.run_until_complete(runner())

    @tb.silence_long_exec_warning()
    def test_signals_and_custom_handler_1(self):
        async def runner():
            PROG = R"""\
import asyncio
import signal
import uvloop

srv = None

async def worker():
    global srv
    cb = lambda *args: None
    srv = await asyncio.start_server(cb, '127.0.0.1', 0)
    print('READY', flush=True)

def handler1():
    print("GOTIT", flush=True)

def handler2():
    assert loop.remove_signal_handler(signal.SIGUSR1)
    print("REMOVED", flush=True)

def handler_hup():
    exit()

loop = """ + self.NEW_LOOP + """
asyncio.set_event_loop(loop)
loop.add_signal_handler(signal.SIGUSR1, handler1)
loop.add_signal_handler(signal.SIGUSR2, handler2)
loop.add_signal_handler(signal.SIGHUP, handler_hup)
loop.create_task(worker())
try:
    loop.run_forever()
finally:
    srv.close()
    loop.run_until_complete(srv.wait_closed())
    loop.close()

"""

            proc = await asyncio.create_subprocess_exec(
                sys.executable, b'-c', PROG,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                loop=self.loop)

            await proc.stdout.readline()

            time.sleep(DELAY)
            proc.send_signal(signal.SIGUSR1)
            time.sleep(DELAY)
            proc.send_signal(signal.SIGUSR1)
            time.sleep(DELAY)
            proc.send_signal(signal.SIGUSR2)
            time.sleep(DELAY)
            proc.send_signal(signal.SIGUSR1)
            time.sleep(DELAY)
            proc.send_signal(signal.SIGUSR1)
            time.sleep(DELAY)
            proc.send_signal(signal.SIGHUP)

            out, err = await proc.communicate()
            self.assertEqual(err, b'')
            self.assertEqual(b'GOTIT\nGOTIT\nREMOVED\n', out)

        self.loop.run_until_complete(runner())

    def test_signals_invalid_signal(self):
        with self.assertRaisesRegex(RuntimeError,
                                    'sig {} cannot be caught'.format(
                                        signal.SIGKILL)):

            self.loop.add_signal_handler(signal.SIGKILL, lambda *a: None)

    def test_signals_coro_callback(self):
        async def coro(): pass
        with self.assertRaisesRegex(TypeError, 'coroutines cannot be used'):
            self.loop.add_signal_handler(signal.SIGHUP, coro)


class Test_UV_Signals(_TestSignal, tb.UVTestCase):
    NEW_LOOP = 'uvloop.new_event_loop()'


class Test_AIO_Signals(_TestSignal, tb.AIOTestCase):
    NEW_LOOP = 'asyncio.new_event_loop()'
