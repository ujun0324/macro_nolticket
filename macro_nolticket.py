"""
자동 클리커 스크립트 (Windows / macOS 공용)
- 실행 후 마우스로 2개의 위치를 클릭하여 지정
- Enter: 위치 지정 완료
- 토글 키: 자동 클릭 시작/일시정지  (macOS: Option(Alt), Windows: F8)
- Esc: 프로그램 종료
"""

import sys
import time
import threading

IS_WINDOWS = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

# ── Windows 전용 초기화 (pynput import 전에 실행해야 함) ──────────────
if IS_WINDOWS:
    import ctypes

    # 화면 배율(125%, 150% 등)에서 클릭 좌표가 어긋나지 않도록 DPI 인식 설정
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    # Windows 기본 타이머 해상도는 약 15ms → time.sleep(0.001)이 제대로 동작하도록 1ms로 설정
    try:
        ctypes.windll.winmm.timeBeginPeriod(1)
    except Exception:
        pass

from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key

# ── 플랫폼별 토글 키 ────────────────────────────────────────────────
if IS_WINDOWS:
    # Windows에서 Alt 단독 입력은 앱 메뉴바를 활성화하고, 한/영 키와도 얽히므로 F8 사용
    TOGGLE_KEYS = {Key.f8}
    TOGGLE_LABEL = "F8"
else:
    TOGGLE_KEYS = {Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr}
    TOGGLE_LABEL = "Option(Alt)"

mouse_controller = MouseController()

positions = []
is_running = False
is_setup_done = False
toggle_held = False  # 키를 꾹 누를 때 발생하는 반복 입력 방지
stop_event = threading.Event()

print("=" * 50)
print("  자동 클리커 - 위치 설정 모드")
print("=" * 50)
print("마우스로 클릭하여 위치 1번을 지정하세요...")

mouse_listener = None
keyboard_listener = None
click_thread = None


def smooth_click(pos):
    """마우스 이동 후 자연스럽게 클릭"""
    mouse_controller.position = pos
    time.sleep(0.001)
    mouse_controller.press(Button.left)
    time.sleep(0.001)
    mouse_controller.release(Button.left)


def click_loop():
    """두 위치를 무한 반복 클릭하는 함수"""
    while not stop_event.is_set():
        if is_running:
            for pos in positions:
                if not is_running or stop_event.is_set():
                    break

                smooth_click(pos)
        else:
            time.sleep(0.001)


def on_click(x, y, button, pressed):
    """마우스 클릭 이벤트 핸들러 (위치 설정용)"""
    global is_setup_done

    if is_setup_done:
        return  # 설정 완료 후에는 무시

    if pressed and button == Button.left:
        positions.append((x, y))
        print(f"  ✅ 위치 {len(positions)} 지정됨: ({x}, {y})")

        if len(positions) == 1:
            print("마우스로 클릭하여 위치 2번을 지정하세요...")
        elif len(positions) == 2:
            print("\n위치 2개 지정 완료!")
            print("▶ Enter를 눌러 설정을 완료하세요.")


def on_key_press(key):
    """키보드 이벤트 핸들러"""
    global is_running, is_setup_done, click_thread, toggle_held

    # ESC: 종료
    if key == Key.esc:
        print("\n🛑 프로그램 종료 중...")
        stop_event.set()
        return False  # 리스너 종료

    # Enter: 위치 지정 완료
    if key == Key.enter and not is_setup_done:
        if len(positions) == 2:
            is_setup_done = True
            print("\n" + "=" * 50)
            print("  설정 완료!")
            print(f"  위치 1: {positions[0]}")
            print(f"  위치 2: {positions[1]}")
            print("=" * 50)
            print(f"▶ {TOGGLE_LABEL} 키: 자동 클릭 시작/정지")
            print("▶ Esc 키: 프로그램 종료")
            print()

            # 클릭 스레드 시작
            click_thread = threading.Thread(target=click_loop, daemon=True)
            click_thread.start()
        else:
            print(f"⚠️  아직 위치를 {2 - len(positions)}개 더 지정해야 합니다.")

    # 토글 키: 자동 클릭 시작/정지
    if key in TOGGLE_KEYS and is_setup_done and not toggle_held:
        toggle_held = True
        is_running = not is_running
        if is_running:
            print("▶ 자동 클릭 시작!")
        else:
            print("⏸ 자동 클릭 일시정지.")


def on_key_release(key):
    """토글 키를 뗐을 때 다시 입력 받을 수 있게 초기화"""
    global toggle_held
    if key in TOGGLE_KEYS:
        toggle_held = False


# 마우스 리스너 시작 (위치 설정용)
mouse_listener = mouse.Listener(on_click=on_click)
mouse_listener.start()

# 키보드 리스너 시작
keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
keyboard_listener.start()

# 프로그램 종료 대기
stop_event.wait()

# 정리
if mouse_listener:
    mouse_listener.stop()
if keyboard_listener:
    keyboard_listener.stop()

if IS_WINDOWS:
    try:
        ctypes.windll.winmm.timeEndPeriod(1)
    except Exception:
        pass

print("프로그램이 종료되었습니다.")
time.sleep(1)  # 콘솔 창이 바로 닫히기 전에 메시지를 볼 수 있게
