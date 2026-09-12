# main.py — Kali Hunter
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDToolbar
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import platform
import threading
import subprocess
import os


class KaliHunterApp(MDApp):

    TERMUX_PREFIX = "/data/data/com.termux/files/usr"
    NMAP_BIN = TERMUX_PREFIX + "/bin/nmap"

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Red"

        screen = MDScreen()

        toolbar = MDToolbar(
            title="Kali Hunter",
            anchor_title="left",
            elevation=4,
            pos_hint={"top": 1},
            md_bg_color=(0.1, 0.1, 0.1, 1),
        )

        root = MDBoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(10),
            pos_hint={"top": 0.9},
        )

        self.target_field = MDTextField(
            hint_text="Цель (IP / домен / подсеть)",
            helper_text="192.168.1.1 или scanme.nmap.org",
            helper_text_mode="on_focus",
            icon_right="target",
            size_hint_x=1,
        )
        root.add_widget(self.target_field)

        modes = [
            ("Быстрое сканирование", "-F -T4"),
            ("Все порты",            "-p- -T4"),
            ("Версии + ОС",          "-sV -O -T4"),
            ("Поиск уязвимостей",    "-sV --script vuln -T4"),
            ("SYN-стелс",            "-sS -T4"),
            ("Ping sweep",           "-sn"),
            ("Проверить root",       "__ROOT_CHECK__"),
        ]
        for text, args in modes:
            btn = MDRaisedButton(
                text=text,
                size_hint_x=1,
                size_hint_y=None,
                height=dp(52),
                md_bg_color=(0.18, 0.18, 0.18, 1),
                text_color=(1, 1, 1, 1),
                on_release=lambda x, a=args: self.start_scan(a),
            )
            root.add_widget(btn)

        self.result_label = MDLabel(
            text="Результаты появятся здесь...",
            halign="left",
            size_hint_y=None,
            markup=True,
        )
        self.result_label.bind(
            width=lambda *x: self.result_label.setter("text_size")(
                self.result_label, (self.result_label.width, None)
            )
        )

        scroll = MDScrollView(size_hint=(1, 1))
        scroll.add_widget(self.result_label)

        card = MDCard(
            orientation="vertical",
            padding=dp(10),
            radius=[12, 12, 12, 12],
            md_bg_color=(0.12, 0.12, 0.12, 1),
            size_hint=(1, 1),
        )
        card.add_widget(scroll)
        root.add_widget(card)

        screen.add_widget(toolbar)
        screen.add_widget(root)
        return screen

    # ---------------- UI handlers ----------------

    def start_scan(self, args):
        if args == "__ROOT_CHECK__":
            self.result_label.text = "[b]Проверяю root...[/b]"
            threading.Thread(target=self._do_root_check, daemon=True).start()
            return

        target = self.target_field.text.strip()
        if not target:
            self.result_label.text = "[color=ff4444]Введи цель[/color]"
            return
        self.result_label.text = f"[b]Сканирую {target}...[/b]"
        threading.Thread(
            target=self._do_scan, args=(target, args), daemon=True
        ).start()

    def _set_result(self, text):
        self.result_label.text = text

    # ---------------- Root helpers ----------------

    def _run_as_root(self, command, timeout=30):
        """
        Запускает команду от root через Magisk.
        Возвращает (stdout, stderr, returncode).
        """
        try:
            r = subprocess.run(
                ["su", "-c", command],
                capture_output=True,
                timeout=timeout,
            )
            return (
                r.stdout.decode(errors="ignore"),
                r.stderr.decode(errors="ignore"),
                r.returncode,
            )
        except FileNotFoundError:
            return "", "su не найден. Magisk не установлен?", 127
        except subprocess.TimeoutExpired:
            return "", "Таймаут: Magisk не ответил на запрос root.", 124
        except Exception as e:
            return "", f"Ошибка вызова su: {e}", 1

    def _has_root(self):
        out, err, code = self._run_as_root("id", timeout=15)
        return ("uid=0" in out) and (code == 0)

    def _path_exists_as_root(self, path):
        out, err, code = self._run_as_root(f"test -x {path}", timeout=10)
        return code == 0

    # ---------------- Root check job ----------------

    def _do_root_check(self):
        info = []

        out, err, code = self._run_as_root("id", timeout=15)
        if "uid=0" in out:
            info.append("[color=44ff44]Root: OK[/color]")
            info.append(f"id: {out.strip()}")
        else:
            info.append("[color=ff4444]Root: НЕТ[/color]")
            info.append(f"stderr: {err.strip()}")
            info.append(
                "\nОткрой Magisk → Superuser → разреши Kali Hunter."
            )
            Clock.schedule_once(lambda dt: self._set_result("\n".join(info)))
            return

        if self._path_exists_as_root(self.NMAP_BIN):
            info.append("[color=44ff44]nmap: найден[/color]")
            ver_out, _, _ = self._run_as_root(
                f"{self.NMAP_BIN} --version | head -n 2", timeout=20
            )
            info.append(ver_out.strip())
        else:
            info.append("[color=ff4444]nmap: НЕ найден[/color]")
            info.append(
                "Установи Termux и выполни:\n"
                "  pkg update && pkg install nmap"
            )

        Clock.schedule_once(lambda dt: self._set_result("\n".join(info)))

    # ---------------- Scan job ----------------

    def _do_scan(self, target, args):
        if platform == "android":
            self._scan_android(target, args)
        else:
            self._scan_desktop(target, args)

    def _scan_android(self, target, args):
        # 1. Проверка root
        if not self._has_root():
            msg = (
                "[color=ff4444]Root не выдан.[/color]\n\n"
                "1) Открой Magisk → Superuser.\n"
                "2) Разреши root для Kali Hunter.\n"
                "3) Нажми «Проверить root» в приложении."
            )
            Clock.schedule_once(lambda dt: self._set_result(msg))
            return

        # 2. Проверка nmap
        if not self._path_exists_as_root(self.NMAP_BIN):
            msg = (
                "[color=ff4444]nmap не найден.[/color]\n\n"
                "Установи Termux и выполни внутри:\n"
                "  pkg update\n"
                "  pkg install nmap"
            )
            Clock.schedule_once(lambda dt: self._set_result(msg))
            return

        # 3. Собираем команду для su -c
        prefix = self.TERMUX_PREFIX
        nmap_cmd = (
            f"LD_LIBRARY_PATH={prefix}/lib "
            f"PATH={prefix}/bin:$PATH "
            f"{self.NMAP_BIN} {args} {target}"
        )

        try:
            out, err, code = self._run_as_root(nmap_cmd, timeout=300)
            result = out if out else err
            if not result.strip():
                result = (
                    f"[color=ff8888]Пустой вывод.[/color]\n"
                    f"exit code: {code}\nstderr: {err}"
                )
        except Exception as e:
            result = f"[color=ff4444]Ошибка:[/color] {e}"

        Clock.schedule_once(lambda dt: self._set_result(result))

    def _scan_desktop(self, target, args):
        try:
            cmd = ["nmap", *args.split(), target]
            out = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, timeout=300
            ).decode(errors="ignore")
        except Exception as e:
            out = f"[color=ff4444]Ошибка:[/color] {e}"
        Clock.schedule_once(lambda dt: self._set_result(out))


if __name__ == "__main__":
    KaliHunterApp().run()
