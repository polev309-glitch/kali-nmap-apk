# main.py
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.utils import platform
import threading
import subprocess


class KaliHunterApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Red"

        screen = MDScreen()

        toolbar = MDTopAppBar(
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

    def start_scan(self, args):
        target = self.target_field.text.strip()
        if not target:
            self.result_label.text = "[color=ff4444]Введи цель[/color]"
            return
        self.result_label.text = f"[b]Сканирую {target}...[/b]"
        threading.Thread(target=self._do_scan, args=(target, args), daemon=True).start()

    def _do_scan(self, target, args):
        # На Android вызываем nmap через Termux, на ПК — напрямую
        if platform == "android":
            cmd = f"nmap {args} {target}"
            try:
                out = subprocess.check_output(
                    ["/data/data/com.termux/files/usr/bin/bash", "-c", cmd],
                    stderr=subprocess.STDOUT, timeout=300
                ).decode(errors="ignore")
            except Exception as e:
                out = f"Ошибка: {e}\nУбедись что Termux установлен и nmap внутри него: pkg install nmap"
        else:
            try:
                out = subprocess.check_output(
                    f"nmap {args} {target}", shell=True,
                    stderr=subprocess.STDOUT, timeout=300
                ).decode(errors="ignore")
            except Exception as e:
                out = f"Ошибка: {e}"

        Clock.schedule_once(lambda dt: self._set_result(out))

    def _set_result(self, text):
        self.result_label.text = text


if __name__ == "__main__":
    KaliHunterApp().run()