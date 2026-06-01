"""
FB Copyright Checker — Dashboard GUI v3
Sidebar: Tài Khoản | Đăng Nhập | Hồ Sơ | Fanpage | Bản Quyền | Logs | Cài Đặt
"""
import json
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Palette ──────────────────────────────────────────────────────────────────
C_BG       = "#0d1117"
C_SIDEBAR  = "#161b22"
C_CARD     = "#1c2128"
C_CARD2    = "#21262d"
C_BORDER   = "#30363d"
C_ACCENT   = "#1877f2"
C_GREEN    = "#2ea043"
C_WARN     = "#d29922"
C_DANGER   = "#da3633"
C_TEXT     = "#e6edf3"
C_DIM      = "#8b949e"
SW         = 230   # sidebar width


# ═════════════════════════════════════════════════════
#  SIDEBAR
# ═════════════════════════════════════════════════════
class Sidebar(ctk.CTkFrame):
    MENU = [
        ("👥", "Tài Khoản",        "accounts"),
        ("👤", "Hồ Sơ",            "profile"),
        ("📄", "Fanpage",          "fanpage"),
        ("🔍", "Kiểm Tra BQ",      "checker"),
        ("📋", "Logs",             "logs"),
        ("⚙️",  "Cài Đặt",         "settings"),
    ]

    def __init__(self, master, on_select, **kw):
        super().__init__(master, width=SW, corner_radius=0, fg_color=C_SIDEBAR, **kw)
        self.on_select = on_select
        self._btns: dict[str, ctk.CTkButton] = {}
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text=" FB Copyright\n Checker",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=C_ACCENT, anchor="w").pack(fill="x", padx=16, pady=(20, 2))
        ctk.CTkLabel(self, text=" v3.0  |  đa tài khoản",
                     font=ctk.CTkFont("Segoe UI", 10), text_color=C_DIM,
                     anchor="w").pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkFrame(self, height=1, fg_color=C_BORDER).pack(fill="x", padx=12)

        for icon, label, key in self.MENU:
            b = ctk.CTkButton(
                self, text=f"  {icon}  {label}", anchor="w",
                font=ctk.CTkFont("Segoe UI", 13),
                fg_color="transparent", hover_color="#21262d",
                text_color=C_DIM, corner_radius=8, height=42,
                command=lambda k=key: self.select(k),
            )
            b.pack(fill="x", padx=8, pady=2)
            self._btns[key] = b

        self.active_lbl = ctk.CTkLabel(
            self, text="● Chưa đăng nhập",
            font=ctk.CTkFont("Segoe UI", 11), text_color=C_DIM)
        self.active_lbl.pack(side="bottom", padx=16, pady=14, anchor="w")

    def select(self, key: str):
        for k, b in self._btns.items():
            b.configure(fg_color=C_ACCENT if k == key else "transparent",
                        text_color=C_TEXT if k == key else C_DIM)
        self.on_select(key)

    def set_active(self, name: str):
        self.active_lbl.configure(text=f"● {name}", text_color=C_GREEN)


# ═════════════════════════════════════════════════════
#  PAGE: ACCOUNTS (multi-account manager)
# ═════════════════════════════════════════════════════
class AccountsPage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self.app = app
        self._build()

    def _build(self):
        # ── Header ──
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(22, 8))
        ctk.CTkLabel(hdr, text="👥 Quản Lý Tài Khoản",
                     font=ctk.CTkFont("Segoe UI", 19, "bold"),
                     text_color=C_TEXT).pack(side="left")
        self.count_lbl = ctk.CTkLabel(hdr, text="",
                                       font=ctk.CTkFont("Segoe UI", 12), text_color=C_DIM)
        self.count_lbl.pack(side="left", padx=10)
        ctk.CTkButton(hdr, text="➕ Thêm nick",    width=115, height=34,
                       fg_color=C_GREEN,  hover_color="#248f39",
                       font=ctk.CTkFont("Segoe UI", 12),
                       command=self._open_add_dialog).pack(side="right", padx=4)
        ctk.CTkButton(hdr, text="📥 Import",       width=95,  height=34,
                       fg_color=C_CARD2, hover_color="#2d333b",
                       text_color=C_TEXT,
                       font=ctk.CTkFont("Segoe UI", 12),
                       command=self._open_import_dialog).pack(side="right", padx=4)
        ctk.CTkButton(hdr, text="📤 Export",       width=95,  height=34,
                       fg_color=C_CARD2, hover_color="#2d333b",
                       text_color=C_TEXT,
                       font=ctk.CTkFont("Segoe UI", 12),
                       command=self._export).pack(side="right", padx=4)

        # ── Table ──
        tf = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=12)
        tf.pack(fill="both", expand=True, padx=28, pady=4)

        style = ttk.Style()
        style.theme_use("clam")
        for s in ("Acc.Treeview", "Acc.Treeview.Heading"):
            style.configure(s, background=C_CARD, foreground=C_TEXT,
                             fieldbackground=C_CARD, rowheight=36,
                             font=("Segoe UI", 12))
        style.configure("Acc.Treeview.Heading", background=C_SIDEBAR,
                         foreground=C_DIM, font=("Segoe UI", 12, "bold"), relief="flat")
        style.map("Acc.Treeview", background=[("selected", C_ACCENT)])

        cols = ("no", "label", "email", "uid", "2fa", "status")
        self.tree = ttk.Treeview(tf, style="Acc.Treeview",
                                  columns=cols, show="headings", selectmode="extended")
        heads = {"no": ("#", 36), "label": ("Tên / Label", 170),
                 "email": ("Email", 200), "uid": ("UID", 120),
                 "2fa": ("2FA", 60), "status": ("Trạng thái", 110)}
        for c, (h, w) in heads.items():
            self.tree.heading(c, text=h, anchor="w" if c != "no" else "center")
            self.tree.column(c, width=w, anchor="w" if c != "no" else "center")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)
        
        self.tree.bind("<Button-3>", self._show_context_menu)

        # ── Action row ──
        act = ctk.CTkFrame(self, fg_color="transparent")
        act.pack(fill="x", padx=28, pady=6)
        ctk.CTkButton(act, text="🔐 Đăng nhập", width=120, height=36,
                       fg_color=C_ACCENT, hover_color="#1464d8",
                       font=ctk.CTkFont("Segoe UI", 12, "bold"),
                       command=self._login_selected).pack(side="left", padx=4)
        ctk.CTkButton(act, text="▶ Kiểm tra Bản quyền", width=170, height=36,
                       fg_color=C_GREEN, hover_color="#248f39",
                       font=ctk.CTkFont("Segoe UI", 12, "bold"),
                       command=self._run_multiple_selected).pack(side="left", padx=4)
        ctk.CTkButton(act, text="✏️ Sửa",               width=80,  height=36,
                       fg_color=C_CARD2, hover_color="#2d333b", text_color=C_TEXT,
                       font=ctk.CTkFont("Segoe UI", 12),
                       command=self._edit_selected).pack(side="left", padx=4)
        ctk.CTkButton(act, text="🗑 Xóa",               width=80,  height=36,
                       fg_color=C_DANGER, hover_color="#b92d2a",
                       font=ctk.CTkFont("Segoe UI", 12),
                       command=self._delete_selected).pack(side="left", padx=4)

    # ── Data ────────────────────────────────────────────────────────────────
    def refresh(self):
        from modules.account_manager import get_manager
        accs = get_manager().get_all()
        self.tree.delete(*self.tree.get_children())
        for i, a in enumerate(accs, 1):
            has2fa = "✓" if a.secret_2fa else "✗"
            status = "Đang dùng" if getattr(self.app, "active_acc_idx", -1) == i - 1 else (
                "Hoạt động" if a.active else "Tắt")
            self.tree.insert("", "end", iid=str(i - 1),
                              values=(i, a.label or "—", a.email, a.uid, has2fa, status))
        self.count_lbl.configure(text=f"({len(accs)} tài khoản)")

    # ── Dialogs ──────────────────────────────────────────────────────────────
    def _open_add_dialog(self, prefill: dict = None, edit_idx: int = None):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Thêm tài khoản" if edit_idx is None else "Sửa tài khoản")
        dlg.geometry("460x480")
        dlg.grab_set()
        dlg.configure(fg_color=C_CARD)

        fields = {}
        defs = prefill or {}
        for lbl, key, show in [
            ("Label (tên hiển thị)", "label",     ""),
            ("Email / SĐT",          "email",     ""),
            ("Mật khẩu",             "password",  "•"),
            ("2FA Secret (base32)",  "secret_2fa",""),
            ("UID (để trống nếu chưa biết)", "uid", ""),
        ]:
            ctk.CTkLabel(dlg, text=lbl, font=ctk.CTkFont("Segoe UI", 12),
                          text_color=C_DIM, anchor="w").pack(fill="x", padx=24, pady=(10, 0))
            var = tk.StringVar(value=defs.get(key, ""))
            ent = ctk.CTkEntry(dlg, textvariable=var, show=show,
                                width=400, height=36,
                                font=ctk.CTkFont("Segoe UI", 12))
            ent.pack(padx=24)
            fields[key] = var

        # OTP preview
        otp_lbl = ctk.CTkLabel(dlg, text="", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                 text_color=C_GREEN)
        otp_lbl.pack()

        def _preview(*_):
            s = fields["secret_2fa"].get().strip()
            if not s:
                otp_lbl.configure(text="")
                return
            try:
                import pyotp
                otp_lbl.configure(text=f"OTP: {pyotp.TOTP(s).now()}", text_color=C_GREEN)
            except Exception:
                otp_lbl.configure(text="Secret không hợp lệ", text_color=C_DANGER)

        fields["secret_2fa"].trace_add("write", _preview)

        def _save():
            from modules.account_manager import Account, get_manager
            mgr = get_manager()
            data = {k: v.get().strip() for k, v in fields.items()}
            if edit_idx is not None:
                existing = mgr.get(edit_idx)
                acc = Account(
                    **data,
                    profile_url=existing.profile_url if existing else "",
                    profile_name=existing.profile_name if existing else "",
                    active=existing.active if existing else True,
                    fanpages=existing.fanpages if existing else [],
                )
                mgr.update(edit_idx, acc)
            else:
                acc = Account(**data)
                if not mgr.add(acc):
                    messagebox.showwarning("Trùng", "Tài khoản đã tồn tại!", parent=dlg)
                    return
            dlg.destroy()
            self.refresh()

        ctk.CTkButton(dlg, text="💾 Lưu", height=40, width=180,
                       fg_color=C_ACCENT, hover_color="#1464d8",
                       font=ctk.CTkFont("Segoe UI", 13, "bold"),
                       command=_save).pack(pady=16)

    def _open_import_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Import nhiều tài khoản")
        dlg.geometry("540x420")
        dlg.grab_set()
        dlg.configure(fg_color=C_CARD)

        ctk.CTkLabel(dlg, text="Nhập mỗi dòng theo định dạng:",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=C_TEXT).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(dlg, text="uid|password|2fa_secret|email\nhoặc: email|password|2fa_secret",
                     font=ctk.CTkFont("Consolas", 12),
                     text_color=C_GREEN).pack(anchor="w", padx=20)

        box = ctk.CTkTextbox(dlg, height=220, font=ctk.CTkFont("Consolas", 12),
                              fg_color=C_BG, text_color=C_TEXT, corner_radius=8)
        box.pack(fill="x", padx=20, pady=10)
        box.insert("end", "# Ví dụ:\n100012345|matkhau123|JBSWY3DP|nick@gmail.com\n")

        result_lbl = ctk.CTkLabel(dlg, text="", font=ctk.CTkFont("Segoe UI", 12),
                                   text_color=C_GREEN)
        result_lbl.pack()

        def _do_import():
            from modules.account_manager import get_manager
            text = box.get("1.0", "end")
            added, skipped = get_manager().import_from_text(text)
            result_lbl.configure(text=f"✓ Đã thêm {added} tài khoản | Bỏ qua {skipped} trùng")
            self.refresh()

        ctk.CTkButton(dlg, text="📥 Import", height=40, width=160,
                       fg_color=C_GREEN, hover_color="#248f39",
                       font=ctk.CTkFont("Segoe UI", 13, "bold"),
                       command=_do_import).pack(pady=8)

    def _export(self):
        from modules.account_manager import get_manager
        text = get_manager().export_to_text()
        dlg = ctk.CTkToplevel(self)
        dlg.title("Export tài khoản")
        dlg.geometry("540x340")
        dlg.configure(fg_color=C_CARD)
        box = ctk.CTkTextbox(dlg, font=ctk.CTkFont("Consolas", 12),
                              fg_color=C_BG, text_color=C_TEXT, corner_radius=8)
        box.pack(fill="both", expand=True, padx=20, pady=20)
        box.insert("end", text)

    def _show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            if iid not in self.tree.selection():
                self.tree.selection_set(iid)
                self.tree.focus(iid)
                
        menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 11))
        menu.add_command(label="✓ Chọn tất cả", command=self._select_all)
        menu.add_command(label="✗ Bỏ chọn tất cả", command=self._deselect_all)
        menu.add_separator()
        menu.add_command(label="🔐 Đăng nhập (nick đang chọn)", command=self._login_selected)
        menu.add_command(label="✏️ Sửa", command=self._edit_selected)
        menu.add_command(label="🗑 Xóa các nick đã chọn", command=self._delete_selected)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _select_all(self):
        self.tree.selection_set(self.tree.get_children())

    def _deselect_all(self):
        self.tree.selection_remove(self.tree.selection())

    def _get_selected_idx(self) -> int:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Chưa chọn", "Vui lòng chọn một tài khoản.")
            return -1
        return int(sel[0])

    def _run_multiple_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Chưa chọn", "Vui lòng chọn tài khoản để quét.")
            return
            
        from modules.account_manager import get_manager
        import subprocess
        mgr = get_manager()
        auto_del = self.app.config.get("checker", {}).get("auto_delete_flagged", False)
        
        opened = 0
        for iid in sel:
            idx = int(iid)
            acc = mgr.get(idx)
            if acc:
                cmd = ["python", "run_cli.py", "--account-id", str(acc.id)]
                if auto_del:
                    cmd.append("--auto-delete")
                # Mở CMD mới
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
                opened += 1
                
        messagebox.showinfo("Thành công", f"Đã mở {opened} cửa sổ dòng lệnh (CMD) để quét độc lập.")

    def _login_selected(self):
        idx = self._get_selected_idx()
        if idx < 0:
            return
        from modules.account_manager import get_manager
        acc = get_manager().get(idx)
        if acc:
            self.app.do_login_account(acc, idx)

    def _edit_selected(self):
        idx = self._get_selected_idx()
        if idx < 0:
            return
        from modules.account_manager import get_manager
        acc = get_manager().get(idx)
        if acc:
            from dataclasses import asdict
            self._open_add_dialog(prefill=asdict(acc), edit_idx=idx)

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Chưa chọn", "Vui lòng chọn tài khoản.")
            return
        if messagebox.askyesno("Xác nhận", f"Xóa {len(sel)} tài khoản đã chọn?"):
            from modules.account_manager import get_manager
            mgr = get_manager()
            idxs = sorted([int(i) for i in sel], reverse=True)
            for idx in idxs:
                mgr.remove(idx)
            self.refresh()


# ═════════════════════════════════════════════════════
#  PAGE: LOGIN (single-account quick login)
# ═════════════════════════════════════════════════════
class LoginPage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self.app = app
        self._build()

    def _build(self):
        card = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=16)
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.50, relheight=0.84)

        ctk.CTkLabel(card, text="🔐 Đăng Nhập Nhanh",
                     font=ctk.CTkFont("Segoe UI", 19, "bold"),
                     text_color=C_TEXT).pack(pady=(26, 4))
        ctk.CTkLabel(card, text="Hoặc dùng tab Tài Khoản để quản lý nhiều nick",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=C_DIM).pack(pady=(0, 16))

        def lbl(t): ctk.CTkLabel(card, text=t, font=ctk.CTkFont("Segoe UI", 12),
                                   text_color=C_DIM, anchor="w").pack(fill="x", padx=38, pady=(6, 0))

        lbl("Email / Số điện thoại")
        self.email_var = tk.StringVar(value=self.app.config.get("facebook", {}).get("email", ""))
        ctk.CTkEntry(card, textvariable=self.email_var, width=360, height=38,
                     font=ctk.CTkFont("Segoe UI", 13),
                     placeholder_text="email@example.com").pack()

        lbl("Mật khẩu")
        self.pass_var = tk.StringVar()
        ctk.CTkEntry(card, textvariable=self.pass_var, show="•", width=360, height=38,
                     font=ctk.CTkFont("Segoe UI", 13),
                     placeholder_text="••••••••").pack()

        lbl("2FA Secret (để trống nếu không dùng)")
        self.tfa_var = tk.StringVar(value=self.app.config.get("facebook", {}).get("2fa_secret", ""))
        ctk.CTkEntry(card, textvariable=self.tfa_var, width=360, height=38,
                     font=ctk.CTkFont("Segoe UI", 13),
                     placeholder_text="JBSWY3DPEHPK3PXP").pack()

        self.otp_lbl = ctk.CTkLabel(card, text="", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                     text_color=C_GREEN)
        self.otp_lbl.pack(pady=2)
        self.tfa_var.trace_add("write", self._preview_otp)

        self.headless_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(card, text="Chế độ ẩn (headless)", variable=self.headless_var,
                         font=ctk.CTkFont("Segoe UI", 12), text_color=C_DIM).pack(pady=6)

        self.login_btn = ctk.CTkButton(card, text="  Đăng Nhập", width=360, height=44,
                                        font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                        fg_color=C_ACCENT, hover_color="#1464d8",
                                        command=self.app.do_login_quick)
        self.login_btn.pack(pady=8)
        self.progress = ctk.CTkProgressBar(card, width=360, mode="indeterminate")
        self.status_lbl = ctk.CTkLabel(card, text="",
                                        font=ctk.CTkFont("Segoe UI", 12), text_color=C_DIM)
        self.status_lbl.pack()

    def _preview_otp(self, *_):
        s = self.tfa_var.get().strip()
        if not s:
            self.otp_lbl.configure(text="")
            return
        try:
            import pyotp
            self.otp_lbl.configure(text=f"OTP: {pyotp.TOTP(s).now()}", text_color=C_GREEN)
        except Exception:
            self.otp_lbl.configure(text="Secret không hợp lệ", text_color=C_DANGER)

    def set_loading(self, on: bool, msg: str = ""):
        if on:
            self.login_btn.configure(state="disabled", text="Đang đăng nhập...")
            self.progress.pack(pady=2)
            self.progress.start()
        else:
            self.login_btn.configure(state="normal", text="  Đăng Nhập")
            self.progress.stop()
            self.progress.pack_forget()
        self.status_lbl.configure(text=msg)

    def get_creds(self):
        return {"email": self.email_var.get().strip(),
                "password": self.pass_var.get(),
                "secret_2fa": self.tfa_var.get().strip(),
                "headless": self.headless_var.get()}


# ═════════════════════════════════════════════════════
#  PAGE: PROFILE
# ═════════════════════════════════════════════════════
class ProfilePage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self.app = app
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="👤 Hồ Sơ",
                     font=ctk.CTkFont("Segoe UI", 19, "bold"),
                     text_color=C_TEXT).pack(anchor="w", padx=28, pady=(22, 8))
        card = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=12)
        card.pack(fill="x", padx=28, pady=4)
        self.name_lbl = self._row_edit(card, "Tên",         "—")
        self.uid_lbl  = self._row(card, "UID",         "—")
        self.url_lbl  = self._row(card, "URL Hồ Sơ", "—")
        ctk.CTkButton(self, text="🔄 Làm mới", height=36, width=140,
                       fg_color=C_ACCENT, hover_color="#1464d8",
                       font=ctk.CTkFont("Segoe UI", 12),
                       command=self.app.do_refresh_profile).pack(anchor="w", padx=28, pady=10)

    def _row(self, p, lbl, val):
        r = ctk.CTkFrame(p, fg_color="transparent")
        r.pack(fill="x", padx=16, pady=7)
        ctk.CTkLabel(r, text=lbl, width=130, font=ctk.CTkFont("Segoe UI", 12),
                     text_color=C_DIM, anchor="w").pack(side="left")
        v = ctk.CTkLabel(r, text=val, font=ctk.CTkFont("Segoe UI", 13, "bold"),
                          text_color=C_TEXT, anchor="w")
        v.pack(side="left")
        return v

    def _row_edit(self, p, lbl, val):
        r = ctk.CTkFrame(p, fg_color="transparent")
        r.pack(fill="x", padx=16, pady=7)
        ctk.CTkLabel(r, text=lbl, width=130, font=ctk.CTkFont("Segoe UI", 12),
                     text_color=C_DIM, anchor="w").pack(side="left")
        v = ctk.CTkEntry(r, width=250, font=ctk.CTkFont("Segoe UI", 13, "bold"),
                          text_color=C_TEXT)
        v.insert(0, val)
        v.pack(side="left")
        
        btn = ctk.CTkButton(r, text="Lưu tên", width=60, height=28,
                             fg_color="#248f39", hover_color="#1d732d",
                             font=ctk.CTkFont("Segoe UI", 11),
                             command=lambda: self._save_name(v.get()))
        btn.pack(side="left", padx=10)
        return v

    def _save_name(self, new_name):
        new_name = new_name.strip()
        if not new_name: return
        self.app.profile_data["name"] = new_name
        
        fb = self.app.config.setdefault("facebook", {})
        fb["profile_name"] = new_name
        self.app.save_config()
        
        idx = getattr(self.app, "active_acc_idx", -1)
        if idx >= 0:
            from modules.account_manager import get_manager
            get_manager().update_profile(idx, self.app.profile_data, self.app.fanpages)
            self.app.pages["accounts"].refresh()
            
        self.app.sidebar.set_active(new_name)
        messagebox.showinfo("Thành công", f"Đã lưu tên cá nhân thành: {new_name}")

    def update(self, p: dict):
        self.name_lbl.delete(0, "end")
        if p.get("name"):
            self.name_lbl.insert(0, p["name"])
        self.uid_lbl.configure(text=p.get("uid") or "—")
        self.url_lbl.configure(text=p.get("profile_url") or "—")


# ═════════════════════════════════════════════════════
#  PAGE: FANPAGE
# ═════════════════════════════════════════════════════
class FanpagePage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self.app = app
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(22, 8))
        ctk.CTkLabel(hdr, text="📄 Fanpage",
                     font=ctk.CTkFont("Segoe UI", 19, "bold"),
                     text_color=C_TEXT).pack(side="left")
        self.count_lbl = ctk.CTkLabel(hdr, text="(0 trang)",
                                       font=ctk.CTkFont("Segoe UI", 12), text_color=C_DIM)
        self.count_lbl.pack(side="left", padx=8)
        
        btn_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="🌐 Get bằng API", width=130, height=34,
                       fg_color="#1877F2", hover_color="#166fe5",
                       font=ctk.CTkFont("Segoe UI", 12, "bold"),
                       command=self.app.do_refresh_fanpages_api).pack(side="right", padx=4)
                       
        ctk.CTkButton(btn_frame, text="🔄 Get bằng Giả Lập", width=140, height=34,
                       fg_color=C_CARD2, hover_color="#2d333b", text_color=C_TEXT,
                       font=ctk.CTkFont("Segoe UI", 12, "bold"),
                       command=self.app.do_refresh_fanpages).pack(side="right", padx=4)

        tf = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=12)
        tf.pack(fill="both", expand=True, padx=28, pady=4)

        style = ttk.Style()
        style.configure("FP.Treeview", background=C_CARD, foreground=C_TEXT,
                         fieldbackground=C_CARD, rowheight=34, font=("Segoe UI", 12))
        style.configure("FP.Treeview.Heading", background=C_SIDEBAR, foreground=C_DIM,
                         font=("Segoe UI", 12, "bold"), relief="flat")
        style.map("FP.Treeview", background=[("selected", C_ACCENT)])

        self.tree = ttk.Treeview(tf, style="FP.Treeview",
                                  columns=("check", "no", "name", "url"), show="headings", selectmode="extended")
        self.tree.heading("check", text="Chọn", anchor="center")
        self.tree.heading("no",   text="#",     anchor="center")
        self.tree.heading("name", text="Tên",   anchor="w")
        self.tree.heading("url",  text="URL",   anchor="w")
        self.tree.column("check", width=50, anchor="center")
        self.tree.column("no",   width=40, anchor="center")
        self.tree.column("name", width=230, anchor="w")
        self.tree.column("url",  width=400, anchor="w")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

        self.sel_lbl = ctk.CTkLabel(self, text="", font=ctk.CTkFont("Segoe UI", 11),
                                     text_color=C_ACCENT, anchor="w")
        self.sel_lbl.pack(fill="x", padx=32, pady=2)
        self.tree.bind("<<TreeviewSelect>>", lambda _: self._on_sel())
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Control-a>", self._select_all)
        self.tree.bind("<Control-A>", self._select_all)
        # Double click to toggle check
        self.tree.bind("<Double-1>", self._on_double_click)

    def _select_all(self, event=None):
        self.tree.selection_set(self.tree.get_children())
        return "break"

    def _on_double_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self._toggle_single_check(iid)

    def _show_context_menu(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            if iid not in self.tree.selection():
                self.tree.selection_set(iid)
                
            menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 11),
                           bg=C_CARD, fg=C_TEXT, activebackground=C_ACCENT)
            menu.add_command(label="Tích chọn các dòng bôi đen (Đổi trạng thái)", command=self._toggle_check)
            menu.add_separator()
            menu.add_command(label="Sao chép ID Fanpage", command=self._copy_id)
            menu.add_command(label="Sao chép Tên Fanpage", command=self._copy_name)
            menu.add_command(label="Sao chép Tên | ID Fanpage", command=self._copy_name_id)
            menu.post(event.x_root, event.y_root)

    def _toggle_single_check(self, iid):
        vals = list(self.tree.item(iid, "values"))
        vals[0] = "☑" if vals[0] == "☐" else "☐"
        self.tree.item(iid, values=vals)

    def _toggle_check(self):
        sel = self.tree.selection()
        if not sel: return
        first_val = self.tree.item(sel[0], "values")[0]
        new_val = "☑" if first_val == "☐" else "☐"
        for iid in sel:
            vals = list(self.tree.item(iid, "values"))
            vals[0] = new_val
            self.tree.item(iid, values=vals)

    def _extract_id(self, url: str) -> str:
        if "id=" in url:
            return url.split("id=")[-1]
        return url.rstrip("/").split("/")[-1]

    def _get_target_items(self):
        checked = [child for child in self.tree.get_children() if self.tree.item(child, "values")[0] == "☑"]
        if checked:
            return checked
        return self.tree.selection()

    def _copy_id(self):
        targets = self._get_target_items()
        ids = []
        for iid in targets:
            url = self.tree.item(iid, "values")[3]
            ids.append(self._extract_id(url))
        if ids:
            self.clipboard_clear()
            self.clipboard_append("\n".join(ids))
            messagebox.showinfo("Đã sao chép", f"Đã sao chép {len(ids)} ID.")

    def _copy_name(self):
        targets = self._get_target_items()
        names = []
        for iid in targets:
            name = self.tree.item(iid, "values")[2]
            names.append(name)
        if names:
            self.clipboard_clear()
            self.clipboard_append("\n".join(names))
            messagebox.showinfo("Đã sao chép", f"Đã sao chép {len(names)} Tên.")

    def _copy_name_id(self):
        targets = self._get_target_items()
        lines = []
        for iid in targets:
            vals = self.tree.item(iid, "values")
            name = vals[2]
            uid = self._extract_id(vals[3])
            lines.append(f"{name}|{uid}")
        if lines:
            self.clipboard_clear()
            self.clipboard_append("\n".join(lines))
            messagebox.showinfo("Đã sao chép", f"Đã sao chép {len(lines)} Tên|ID.")

    def _on_sel(self):
        s = self.tree.selection()
        if s:
            self.sel_lbl.configure(text="URL: " + str(self.tree.item(s[0])["values"][3]))

    def populate(self, pages: list):
        self.tree.delete(*self.tree.get_children())
        for i, p in enumerate(pages, 1):
            self.tree.insert("", "end", values=("☐", i, p.get("name", ""), p.get("url", "")))
        self.count_lbl.configure(text=f"({len(pages)} trang)")


# ═════════════════════════════════════════════════════
#  PAGE: CHECKER
# ═════════════════════════════════════════════════════
class CheckerPage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self.app = app
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="🔍 Kiểm Tra Bản Quyền",
                     font=ctk.CTkFont("Segoe UI", 19, "bold"),
                     text_color=C_TEXT).pack(anchor="w", padx=28, pady=(22, 2))
        ctk.CTkLabel(self, text="Quét profile + fanpage qua trang Appeals của Facebook",
                     font=ctk.CTkFont("Segoe UI", 11), text_color=C_DIM).pack(anchor="w", padx=28)

        opt = ctk.CTkFrame(self, fg_color="transparent")
        opt.pack(fill="x", padx=28, pady=10)
        self.auto_var = tk.BooleanVar()
        ctk.CTkCheckBox(opt, text="Tự động xóa bài vi phạm", variable=self.auto_var,
                         font=ctk.CTkFont("Segoe UI", 13), text_color=C_TEXT).pack(side="left")

        self.loop_var = tk.StringVar(value="1 Vòng")
        self.loop_menu = ctk.CTkOptionMenu(opt, variable=self.loop_var, 
                                           values=["1 Vòng", "N Vòng", "Vô Hạn"],
                                           width=100, command=self._on_loop_change)
        self.loop_menu.pack(side="left", padx=(20, 5))
        
        self.loop_count_var = tk.StringVar(value="2")
        self.loop_entry = ctk.CTkEntry(opt, textvariable=self.loop_count_var, width=40)
        self.loop_entry.pack(side="left", padx=5)
        self.loop_entry.configure(state="disabled")

        ctk.CTkLabel(opt, text="Nghỉ (s):", font=ctk.CTkFont("Segoe UI", 12)).pack(side="left", padx=(10, 2))
        self.sleep_var = tk.StringVar(value="60")
        self.sleep_entry = ctk.CTkEntry(opt, textvariable=self.sleep_var, width=45)
        self.sleep_entry.pack(side="left", padx=2)

        self.run_btn = ctk.CTkButton(opt, text="▶ Quét Tất Cả",
                                      fg_color=C_GREEN, hover_color="#248f39",
                                      height=40, width=120,
                                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                      command=self.app.do_run_checker_all)
        self.run_btn.pack(side="right", padx=5)

        self.run_sel_btn = ctk.CTkButton(opt, text="▶ Quét Đã Chọn",
                                      fg_color=C_ACCENT, hover_color="#166fe5",
                                      height=40, width=130,
                                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                      command=self.app.do_run_checker_selected)
        self.run_sel_btn.pack(side="right", padx=5)
        
        self.stop_btn = ctk.CTkButton(opt, text="⏹  Dừng Quét",
                                       fg_color=C_DANGER, hover_color="#b92d2a",
                                       height=40, width=120,
                                       font=ctk.CTkFont("Segoe UI", 13, "bold"),
                                       command=self.app.do_stop_checker,
                                       state="disabled")
        self.stop_btn.pack(side="right", padx=5)

        # Stats
        stats = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=12)
        stats.pack(fill="x", padx=28, pady=4)
        self.s_total   = self._stat(stats, "Vi Phạm", "0")
        self.s_deleted = self._stat(stats, "Đã Xóa",  "0")
        self.s_pages   = self._stat(stats, "Trang Quét", "0")

        self.progress  = ctk.CTkProgressBar(self, mode="indeterminate")
        self.prog_lbl  = ctk.CTkLabel(self, text="",
                                       font=ctk.CTkFont("Segoe UI", 11), text_color=C_DIM)

        # Results
        tf = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=12)
        tf.pack(fill="both", expand=True, padx=28, pady=6)
        style = ttk.Style()
        style.configure("CK.Treeview", background=C_CARD, foreground=C_TEXT,
                         fieldbackground=C_CARD, rowheight=30, font=("Segoe UI", 11))
        style.configure("CK.Treeview.Heading", background=C_SIDEBAR, foreground=C_DIM,
                         font=("Segoe UI", 11, "bold"), relief="flat")
        style.map("CK.Treeview", background=[("selected", C_ACCENT)])
        self.tree = ttk.Treeview(tf, style="CK.Treeview",
                                  columns=("ctx", "title", "url", "st"), show="headings")
        for c, h, w in [("ctx","Nguồn",100),("title","Tiêu đề",260),
                         ("url","URL",220),("st","Trạng thái",90)]:
            self.tree.heading(c, text=h, anchor="w")
            self.tree.column(c, width=w, anchor="w")
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

    def _on_loop_change(self, choice):
        if choice == "N Vòng":
            self.loop_entry.configure(state="normal")
        else:
            self.loop_entry.configure(state="disabled")

    def _stat(self, p, lbl, val):
        b = ctk.CTkFrame(p, fg_color="transparent")
        b.pack(side="left", expand=True, pady=10)
        v = ctk.CTkLabel(b, text=val, font=ctk.CTkFont("Segoe UI", 26, "bold"), text_color=C_ACCENT)
        v.pack()
        ctk.CTkLabel(b, text=lbl, font=ctk.CTkFont("Segoe UI", 11), text_color=C_DIM).pack()
        return v

    def set_running(self, on: bool):
        if on:
            self.run_btn.configure(state="disabled", text="Đang quét...")
            self.stop_btn.configure(state="normal")
            self.progress.pack(fill="x", padx=28, pady=2)
            self.progress.start()
            self.prog_lbl.pack(anchor="w", padx=28)
        else:
            self.run_btn.configure(state="normal", text="▶  Bắt Đầu Quét")
            self.stop_btn.configure(state="disabled")
            self.progress.stop()
            self.progress.pack_forget()
            self.prog_lbl.pack_forget()

    def set_prog(self, msg): self.prog_lbl.configure(text=msg)
    def update_stats(self, t, d, p):
        self.s_total.configure(text=str(t))
        self.s_deleted.configure(text=str(d))
        self.s_pages.configure(text=str(p))
    def add_row(self, d):
        self.tree.insert("", "end", values=(
            d.get("context",""), d.get("title","")[:58], d.get("post_url",""), d.get("status","")))
    def clear(self): self.tree.delete(*self.tree.get_children())
    def populate_violations(self, v_list: list):
        self.clear()
        for d in v_list:
            self.add_row(d)
        self.update_stats(len(v_list), 0, 0)


# ═════════════════════════════════════════════════════
#  PAGE: LOGS
# ═════════════════════════════════════════════════════
class LogsPage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self.app = app
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(22, 6))
        ctk.CTkLabel(hdr, text="📋 Logs",
                     font=ctk.CTkFont("Segoe UI", 19, "bold"),
                     text_color=C_TEXT).pack(side="left")
        ctk.CTkButton(hdr, text="🗑 Xóa", width=80, height=32,
                       fg_color=C_CARD2, hover_color="#2d333b", text_color=C_DIM,
                       font=ctk.CTkFont("Segoe UI", 11),
                       command=self.clear).pack(side="right")
        self.box = ctk.CTkTextbox(self, fg_color=C_CARD, text_color=C_TEXT,
                                   font=ctk.CTkFont("Consolas", 12),
                                   corner_radius=12, wrap="word")
        self.box.pack(fill="both", expand=True, padx=28, pady=4)

    def append(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.box.configure(state="normal")
        self.box.insert("end", f"[{ts}] {msg}\n")
        self.box.see("end")

    def clear(self):
        self.box.configure(state="normal")
        self.box.delete("1.0", "end")


# ═════════════════════════════════════════════════════
#  PAGE: SETTINGS
# ═════════════════════════════════════════════════════
class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        super().__init__(master, fg_color=C_BG, **kw)
        self.app = app
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="⚙️ Cài Đặt",
                     font=ctk.CTkFont("Segoe UI", 19, "bold"),
                     text_color=C_TEXT).pack(anchor="w", padx=28, pady=(22, 14))
        card = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=12)
        card.pack(fill="x", padx=28, pady=4)

        sel = self.app.config
        self.headless_var  = self._toggle(card, "Chế độ ẩn (headless)",
                                            sel.get("selenium", {}).get("headless", False))
        self.autodel_var   = self._toggle(card, "Tự động xóa vi phạm",
                                            sel.get("checker", {}).get("auto_delete_flagged", False))

        r = ctk.CTkFrame(card, fg_color="transparent")
        r.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(r, text="Chu kỳ quét (giây)", width=220,
                     font=ctk.CTkFont("Segoe UI", 13), text_color=C_TEXT, anchor="w").pack(side="left")
        self.interval_var = tk.StringVar(value=str(sel.get("checker", {}).get("scan_interval_seconds", 60)))
        ctk.CTkEntry(r, textvariable=self.interval_var, width=80,
                     font=ctk.CTkFont("Segoe UI", 13)).pack(side="right")

        ctk.CTkButton(self, text="💾 Lưu", height=40, width=140,
                       fg_color=C_ACCENT, hover_color="#1464d8",
                       font=ctk.CTkFont("Segoe UI", 13, "bold"),
                       command=self._save).pack(anchor="w", padx=28, pady=14)

    def _toggle(self, p, lbl, val):
        r = ctk.CTkFrame(p, fg_color="transparent")
        r.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(r, text=lbl, width=220, font=ctk.CTkFont("Segoe UI", 13),
                     text_color=C_TEXT, anchor="w").pack(side="left")
        var = tk.BooleanVar(value=val)
        ctk.CTkSwitch(r, text="", variable=var).pack(side="right")
        return var

    def _save(self):
        c = self.app.config
        c.setdefault("selenium", {})["headless"] = self.headless_var.get()
        c.setdefault("checker", {})["auto_delete_flagged"] = self.autodel_var.get()
        try:
            c["checker"]["scan_interval_seconds"] = int(self.interval_var.get())
        except ValueError:
            pass
        self.app.save_config()
        messagebox.showinfo("OK", "Đã lưu cài đặt!")


# ═════════════════════════════════════════════════════
#  MAIN APP
# ═════════════════════════════════════════════════════
class App(ctk.CTk):
    CONFIG_PATH = "config.json"

    def __init__(self):
        super().__init__()
        self.title("FB Copyright Checker v1.0.0")
        self.geometry("1140x700")
        self.minsize(940, 600)
        self.configure(fg_color=C_BG)

        self.config       = self._load_cfg()
        self.driver       = None
        self._chrome_profile_dir = None
        self.profile_data : dict = {}
        self.fanpages     : list = []
        self.active_acc_idx: int = -1
        self._q           = queue.Queue()
        self.stop_checker_event = threading.Event()

        self._build()
        self.sidebar.select("accounts")
        self.after(120, self._poll)

    # ── Layout ──────────────────────────────────────────────────────────────
    def _build(self):
        self.sidebar = Sidebar(self, self._show)
        self.sidebar.pack(side="left", fill="y")
        ctk.CTkFrame(self, width=1, fg_color=C_BORDER).pack(side="left", fill="y")
        self.content = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        self.pages = {
            "accounts": AccountsPage(self.content, self),
            "login"   : LoginPage(self.content, self),
            "profile" : ProfilePage(self.content, self),
            "fanpage" : FanpagePage(self.content, self),
            "checker" : CheckerPage(self.content, self),
            "logs"    : LogsPage(self.content, self),
            "settings": SettingsPage(self.content, self),
        }

    def _show(self, key: str):
        for p in self.pages.values():
            p.place_forget()
        self.pages[key].place(relx=0, rely=0, relwidth=1, relheight=1)
        if key == "accounts":
            self.pages["accounts"].refresh()

    # ── Config ──────────────────────────────────────────────────────────────
    def _load_cfg(self) -> dict:
        if os.path.exists(self.CONFIG_PATH):
            with open(self.CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_config(self):
        with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    # ── Queue ────────────────────────────────────────────────────────────────
    def _poll(self):
        try:
            while True:
                self._dispatch(self._q.get_nowait())
        except queue.Empty:
            pass
        self.after(120, self._poll)

    def _dispatch(self, msg: dict):
        k = msg.get("kind")
        if k == "log":
            self.pages["logs"].append(msg["text"])
        elif k == "login_done":
            self._on_login_done(msg)
        elif k == "profile_done":
            self._on_profile_done(msg)
        elif k == "fanpages_done":
            self._on_fanpages_done(msg)
        elif k == "checker_log":
            self.pages["checker"].set_prog(msg["text"])
            self.pages["logs"].append(msg["text"])
        elif k == "checker_loop_done":
            self._on_checker_loop_done(msg)
        elif k == "checker_done":
            self._on_checker_done(msg)

    def _log(self, t): self._q.put({"kind": "log", "text": t})

    # ── Login (quick) ────────────────────────────────────────────────────────
    def do_login_quick(self):
        creds = self.pages["login"].get_creds()
        if not creds["email"] or not creds["password"]:
            messagebox.showwarning("Thiếu thông tin", "Nhập email và mật khẩu.")
            return
        fb = self.config.setdefault("facebook", {})
        fb["email"] = creds["email"]
        fb["2fa_secret"] = creds["secret_2fa"]
        self.config.setdefault("selenium", {})["headless"] = creds["headless"]
        self.save_config()
        self.pages["login"].set_loading(True, "Đang khởi động Chrome...")
        threading.Thread(target=self._login_thread, args=(creds,), daemon=True).start()

    def do_login_account(self, acc, idx: int):
        creds = {"email": acc.email, "password": acc.password,
                 "secret_2fa": acc.secret_2fa,
                 "headless": self.config.get("selenium", {}).get("headless", False),
                 "uid": acc.uid}
        self.active_acc_idx = idx
        self._log(f"Bắt đầu đăng nhập tài khoản: {acc.display_name}...")
        self.pages["login"].set_loading(True, f"Đang đăng nhập {acc.display_name}...")
        threading.Thread(target=self._login_thread, args=(creds, idx), daemon=True).start()

    def _login_thread(self, creds: dict, acc_idx: int = -1):
        _saved_fb = {}
        _saved_headless = None
        try:
            import sys
            workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, workspace_dir)
            from modules.fb_login import build_driver, login as fb_login
            from modules.config_loader import CONFIG

            _saved_fb = {k: CONFIG["facebook"].get(k) for k in ("email", "password", "2fa_secret")}
            _saved_headless = CONFIG["selenium"].get("headless")
            CONFIG["facebook"]["email"]      = creds["email"]
            CONFIG["facebook"]["password"]   = creds["password"]
            CONFIG["facebook"]["2fa_secret"] = creds["secret_2fa"]
            CONFIG["selenium"]["headless"]   = creds["headless"]

            self._log("Đang khởi động trình duyệt...")
            if self.driver:
                try: self.driver.quit()
                except Exception: pass

            uid = creds.get("uid", "")
            if uid:
                from agent.act import build_driver_for_account, chrome_profile_dir
                self.driver = build_driver_for_account(uid)
                self._chrome_profile_dir = chrome_profile_dir(uid)
            else:
                self.driver = build_driver()
                self._chrome_profile_dir = os.path.join(workspace_dir, 'chrome_profile', 'default')

            self._log("Đang đăng nhập...")
            ok = fb_login(self.driver)
            self._q.put({"kind": "login_done", "ok": ok,
                          "label": creds["email"], "acc_idx": acc_idx})

            # Login completion only
        except Exception as e:
            # Ghi nhận crash vào last_error.json
            try:
                import traceback
                tb = traceback.format_exc()
                workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                import re
                matches = re.findall(r'File "([^"]+)"\,\s+line\s+(\d+)', tb)
                referenced_files = []
                for filepath, line in matches:
                    abs_path = os.path.abspath(filepath) if os.path.isabs(filepath) else os.path.join(workspace_dir, filepath)
                    if os.path.exists(abs_path) and abs_path.startswith(workspace_dir):
                        rel = os.path.relpath(abs_path, workspace_dir)
                        if rel not in referenced_files and "ai_runner.py" not in rel:
                            referenced_files.append(rel)
                error_data = {
                    "feature": "Đăng nhập Facebook",
                    "step": "Lỗi trong luồng đăng nhập nền",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "referenced_files": referenced_files,
                    "traceback": tb
                }
                with open(os.path.join(workspace_dir, "last_error.json"), "w", encoding="utf-8") as f:
                    json.dump(error_data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
            self._q.put({"kind": "login_done", "ok": False,
                          "label": "", "error": str(e), "acc_idx": acc_idx})
        finally:
            # Luôn khôi phục CONFIG sau khi login (bất kể thành công hay thất bại)
            if _saved_fb:
                CONFIG["facebook"].update(_saved_fb)
            if _saved_headless is not None:
                CONFIG["selenium"]["headless"] = _saved_headless

    def _on_login_done(self, msg: dict):
        ok = msg["ok"]
        self.pages["login"].set_loading(False,
            "✓ Đăng nhập thành công!" if ok else f"✗ Lỗi: {msg.get('error','')}")
        if ok:
            self.sidebar.set_active(msg["label"])
            self._show("profile")
            self.sidebar.select("profile")
            
            # Tự động tải dữ liệu cũ (cache) từ database nếu đăng nhập từ acc_idx
            idx = msg.get("acc_idx", -1)
            if idx >= 0:
                from modules.account_manager import get_manager
                acc = get_manager().get(idx)
                if acc:
                    from agent.act import chrome_profile_dir
                    self._chrome_profile_dir = chrome_profile_dir(acc.uid)
                if acc and (acc.profile_name or acc.fanpages):
                    self.profile_data = {
                        "name": acc.profile_name or acc.label or acc.uid,
                        "uid": acc.uid,
                        "profile_url": acc.profile_url
                    }
                    self.fanpages = acc.fanpages
                    self.pages["profile"].update(self.profile_data)
                    self.pages["fanpage"].populate(self.fanpages)
                    self._log(f"Đã tải {len(self.fanpages)} fanpage và thông tin cá nhân từ cơ sở dữ liệu.")
                    
                    from modules.database import Database
                    db = Database()
                    v_list = db.get_violations(acc.uid)
                    db.close()
                    if v_list:
                        self.pages["checker"].populate_violations(v_list)
                        self._log(f"Đã tải {len(v_list)} bài vi phạm cũ từ cơ sở dữ liệu.")
        else:
            self._log(f"Đăng nhập thất bại: {msg.get('error','')}")

    def _on_profile_done(self, msg: dict):
        self.profile_data = msg["profile"]
        self.pages["profile"].update(self.profile_data)
        
        uid = self.profile_data.get("uid", "")
        if uid:
            from agent.act import chrome_profile_dir
            self._chrome_profile_dir = chrome_profile_dir(uid)

        fb = self.config.setdefault("facebook", {})
        fb.update({"profile_url": self.profile_data.get("profile_url", ""),
                   "profile_name": self.profile_data.get("name", ""),
                   "uid": uid})
        self.save_config()

        # Hiển thị tên tài khoản (nickname) trên sidebar status
        nickname = self.profile_data.get("name") or self.profile_data.get("uid") or "Đã đăng nhập"
        self.sidebar.set_active(nickname)

        # Cập nhật vào account manager nếu login từ account
        idx = msg.get("acc_idx", -1)
        if idx >= 0:
            from modules.account_manager import get_manager
            get_manager().update_profile(idx, self.profile_data, self.fanpages)
            self.pages["accounts"].refresh()

    def _on_fanpages_done(self, msg: dict):
        self.fanpages = msg["pages"]
        self.pages["fanpage"].populate(self.fanpages)
        self._log(f"Tìm thấy {len(self.fanpages)} fanpage")
        fp = [{"name": p.get("name"), "url": p.get("url")} for p in self.fanpages]
        self.config.setdefault("facebook", {})["fanpages"] = fp
        self.save_config()

        # Cập nhật vào account manager để lưu cache
        idx = msg.get("acc_idx", -1)
        if idx >= 0:
            from modules.account_manager import get_manager
            get_manager().update_profile(idx, self.profile_data, self.fanpages)
            self.pages["accounts"].refresh()

    # ── Refresh ──────────────────────────────────────────────────────────────
    def _need_driver(self, action: str = "") -> bool:
        if not self.driver:
            messagebox.showwarning("Chưa đăng nhập", f"Hãy đăng nhập trước khi {action}.")
            return False
        return True

    def do_refresh_profile(self):
        if not self._need_driver("làm mới hồ sơ"): return
        threading.Thread(target=self._do_refresh_profile, daemon=True).start()

    def _do_refresh_profile(self):
        from modules.fb_profile import get_profile_info, save_profile_to_config
        from modules.copyright_checker import switch_to_profile
        self._log("Đảm bảo đang ở trang cá nhân gốc...")
        switch_to_profile(self.driver)
        
        p = get_profile_info(self.driver)
        save_profile_to_config(p)
        self._q.put({"kind": "profile_done", "profile": p, "acc_idx": self.active_acc_idx})

    def do_refresh_fanpages(self):
        if not self._need_driver("làm mới fanpage"): return
        threading.Thread(target=self._do_refresh_fanpages, daemon=True).start()

    def _do_refresh_fanpages(self):
        from modules.fb_profile import get_fanpages
        self._log("Đang lấy danh sách fanpage bằng giả lập...")
        pages = get_fanpages(self.driver)
        self._q.put({"kind": "fanpages_done", "pages": pages, "acc_idx": self.active_acc_idx})

    def do_refresh_fanpages_api(self):
        token = ctk.dialogs.CTkInputDialog(text="Vui lòng nhập Access Token của bạn (EAAG...):", title="Nhập API Token").get_input()
        if not token:
            return
        threading.Thread(target=self._do_refresh_fanpages_api, args=(token,), daemon=True).start()

    def _do_refresh_fanpages_api(self, token: str):
        from modules.fb_profile import get_fanpages_by_api
        self._log("Đang lấy danh sách fanpage bằng API...")
        pages = get_fanpages_by_api(token)
        if pages:
            self._q.put({"kind": "fanpages_done", "pages": pages, "acc_idx": self.active_acc_idx})
        else:
            self._log("Không lấy được trang nào từ API hoặc Token không hợp lệ.")

    # ── Copyright Checker ────────────────────────────────────────────────────
    # ── Checker Actions ──────────────────────────────────────────────────────
    def _get_loop_config(self):
        choice = self.pages["checker"].loop_var.get()
        if choice == "1 Vòng": return 1
        elif choice == "N Vòng":
            try: return int(self.pages["checker"].loop_count_var.get())
            except ValueError: return 1
        return 0

    def _prepare_checker(self):
        if not self._need_driver("kiểm tra bản quyền"): return False
        self.stop_checker_event.clear()
        self.pages["checker"].set_running(True)
        self.pages["checker"].clear()
        return True

    def _ensure_driver_ready(self) -> bool:
        try:
            if self.driver:
                _ = self.driver.current_window_handle
                return True
        except Exception:
            pass
            
        self._log("Trình duyệt đã đóng. Đang mở lại Chrome...")
        try:
            import sys
            workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, workspace_dir)
            from modules.fb_login import build_driver, login as fb_login
            from modules.config_loader import CONFIG
            
            creds = None
            uid = ""
            if self.active_acc_idx >= 0:
                from modules.account_manager import get_manager
                acc = get_manager().get(self.active_acc_idx)
                if acc:
                    creds = {"email": acc.email, "password": acc.password, "secret_2fa": acc.secret_2fa}
                    uid = acc.uid
            else:
                creds = self.pages["login"].get_creds()
                
            if not creds or not creds.get("email") or not creds.get("password"):
                self._log("Không tìm thấy mật khẩu để đăng nhập lại tự động.")
                return False
                
            _saved_fb = {k: CONFIG["facebook"].get(k) for k in ("email", "password", "2fa_secret")}
            CONFIG["facebook"]["email"]      = creds["email"]
            CONFIG["facebook"]["password"]   = creds["password"]
            CONFIG["facebook"]["2fa_secret"] = creds["secret_2fa"]
            
            if uid:
                from agent.act import build_driver_for_account, chrome_profile_dir
                self.driver = build_driver_for_account(uid)
                self._chrome_profile_dir = chrome_profile_dir(uid)
            else:
                self.driver = build_driver()
                self._chrome_profile_dir = os.path.join(workspace_dir, 'chrome_profile', 'default')
            ok = fb_login(self.driver)
            
            if _saved_fb:
                CONFIG["facebook"].update(_saved_fb)
                
            if ok:
                self._log("Đã đăng nhập lại thành công.")
                return True
            else:
                self._log("Đăng nhập lại thất bại.")
                return False
        except Exception as e:
            self._log(f"Lỗi khi mở lại trình duyệt: {e}")
            return False

    def do_run_checker_all(self):
        if not self._prepare_checker(): return
        auto = self.pages["checker"].auto_var.get()
        loops = self._get_loop_config()
        threading.Thread(target=self._checker_thread, args=(auto, self.fanpages, loops), daemon=True).start()

    def do_run_checker_selected(self):
        if not self._prepare_checker(): return
        # Get selected fanpages from FanpagePage
        targets = self.pages["fanpage"]._get_target_items()
        if not targets:
            messagebox.showinfo("Lỗi", "Vui lòng chọn (tích ☑ hoặc bôi đen) ít nhất 1 fanpage ở tab Fanpage.")
            self.pages["checker"].set_running(False)
            return
            
        selected_pages = []
        for iid in targets:
            name = self.pages["fanpage"].tree.item(iid, "values")[2]
            url = self.pages["fanpage"].tree.item(iid, "values")[3]
            selected_pages.append({"name": name, "url": url})
            
        auto = self.pages["checker"].auto_var.get()
        loops = self._get_loop_config()
        threading.Thread(target=self._checker_thread, args=(auto, selected_pages, loops), daemon=True).start()

    def do_stop_checker(self):
        self.stop_checker_event.set()
        self._log("Đang yêu cầu dừng quét bản quyền...")
        self.pages["checker"].set_prog("Đang yêu cầu dừng...")

    def _checker_thread(self, auto_delete: bool, pages_to_scan: list, max_loops: int = 1):
        db = None
        try:
            from modules.copyright_checker import run_full_copyright_check
            from modules.database import Database
            db = Database()
            
            loop_count = 0
            final_result = {"total_appeals": 0, "deleted": 0, "details": []}
            while not self.stop_checker_event.is_set():
                loop_count += 1
                if max_loops > 0:
                    self._log(f"--- BẮT ĐẦU QUÉT VÒNG {loop_count}/{max_loops} ---")
                else:
                    self._log(f"--- BẮT ĐẦU QUÉT VÒNG {loop_count} (VÔ HẠN) ---")

                if not self._ensure_driver_ready():
                    self._log("Không thể khôi phục trình duyệt. Dừng tiến trình quét.")
                    break

                result = run_full_copyright_check(
                    self.driver, db, pages_to_scan, auto_delete=auto_delete,
                    log_callback=lambda m: self._q.put({"kind": "checker_log", "text": m}),
                    account_name=self.profile_data.get("name", "GUI"),
                    stop_event=self.stop_checker_event,
                    profile_dir=getattr(self, "_chrome_profile_dir", None),
                )
                # Cập nhật driver nếu Chrome đã bị rebuild trong quá trình quét
                if result.get("driver") and result["driver"] is not self.driver:
                    self.driver = result["driver"]
                final_result = result
                
                self._q.put({"kind": "checker_loop_done", "result": result, "loop": loop_count, "max_loops": max_loops})
                
                if self.stop_checker_event.is_set():
                    break
                    
                if max_loops > 0 and loop_count >= max_loops:
                    break
                    
                # Close driver to save resources during sleep
                try:
                    if self.driver:
                        self.driver.quit()
                        self.driver = None
                        self._log("Đã đóng trình duyệt tạm thời để tiết kiệm tài nguyên hệ thống.")
                except Exception:
                    pass
                    
                try:
                    interval = int(self.pages["checker"].sleep_var.get())
                except ValueError:
                    interval = 60
                self._log(f"Đợi {interval} giây trước khi quét vòng tiếp theo...")
                self._q.put({"kind": "checker_log", "text": f"Đợi {interval} giây..."})
                
                wait_time = 0
                while wait_time < interval and not self.stop_checker_event.is_set():
                    time.sleep(1)
                    wait_time += 1
                    
            self._q.put({"kind": "checker_done", "result": final_result})
        except Exception as e:
            # Ghi nhận crash vào last_error.json
            try:
                import traceback
                tb = traceback.format_exc()
                workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                import re
                matches = re.findall(r'File "([^"]+)"\,\s+line\s+(\d+)', tb)
                referenced_files = []
                for filepath, line in matches:
                    abs_path = os.path.abspath(filepath) if os.path.isabs(filepath) else os.path.join(workspace_dir, filepath)
                    if os.path.exists(abs_path) and abs_path.startswith(workspace_dir):
                        rel = os.path.relpath(abs_path, workspace_dir)
                        if rel not in referenced_files and "ai_runner.py" not in rel:
                            referenced_files.append(rel)
                error_data = {
                    "feature": "Kiểm tra bản quyền Appeals",
                    "step": "Lỗi trong luồng kiểm tra nền",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "referenced_files": referenced_files,
                    "traceback": tb
                }
                with open(os.path.join(workspace_dir, "last_error.json"), "w", encoding="utf-8") as f:
                    json.dump(error_data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
            self._q.put({"kind": "checker_done", "result": {"total_appeals": 0, "deleted": 0, "details": []}, "error": str(e)})
        finally:
            if db:
                db.close()

    def _on_checker_loop_done(self, msg: dict):
        r = msg["result"]
        loop = msg["loop"]
        max_loops = msg["max_loops"]
        
        self.pages["checker"].clear()
        self.pages["checker"].update_stats(r["total_appeals"], r["deleted"], 1 + len(self.fanpages))
        for d in r["details"]:
            self.pages["checker"].add_row(d)
            
        if max_loops > 0 and loop >= max_loops:
            pass
        elif not self.stop_checker_event.is_set():
            self._log(f"Hoàn tất vòng {loop}. Vi phạm: {r['total_appeals']} | Đã xóa: {r['deleted']}")

    def _on_checker_done(self, msg: dict):
        self.pages["checker"].set_running(False)
        if "error" in msg:
            self._log(f"✗ Quét thất bại: {msg['error']}")
            messagebox.showerror("Lỗi quét", f"Đã xảy ra lỗi khi quét: {msg['error']}")
            return
            
        r = msg["result"]
        self.pages["checker"].update_stats(r["total_appeals"], r["deleted"], 1 + len(self.fanpages))
        for d in r["details"]:
            self.pages["checker"].add_row(d)
            
        if self.stop_checker_event.is_set():
            self._log(f"Đã dừng quét. Kết quả tạm thời: {r['total_appeals']} vi phạm | {r['deleted']} đã xóa")
            # Show user feedback that the scan was stopped
            from tkinter import messagebox
            messagebox.showinfo("Quét dừng", "Quét đã dừng bởi người dùng.")
        else:
            self._log(f"Hoàn tất: {r['total_appeals']} vi phạm | {r['deleted']} đã xóa")

    # ── Close ────────────────────────────────────────────────────────────────
    def on_close(self):
        if self.driver:
            try: self.driver.quit()
            except Exception: pass
        self.destroy()


def run_dashboard():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    run_dashboard()
