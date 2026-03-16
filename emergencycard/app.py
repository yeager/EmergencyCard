#!/usr/bin/env python3
"""EmergencyCard - Digitalt nodkort for nodsituationer."""

import gi
import json
import os
import sys
import tempfile

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gdk, Pango, GdkPixbuf
from emergencycard.i18n import _

APP_ID = "se.emergencycard.app"
DATA_DIR = os.path.join(GLib.get_user_data_dir(), "emergency-card")
DATA_FILE = os.path.join(DATA_DIR, "card.json")

DEFAULT_DATA = {
    "namn": "",
    "personnummer": "",
    "diagnoser": "",
    "mediciner": "",
    "allergier": "",
    "kommunikation": "",
    "kontakter": [{"namn": "", "telefon": "", "relation": ""}],
    "anteckningar": "",
}


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all keys exist
            for key in DEFAULT_DATA:
                if key not in data:
                    data[key] = DEFAULT_DATA[key]
            return data
    return json.loads(json.dumps(DEFAULT_DATA))


def save_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_qr_pixbuf(text, size=280):
    """Generate QR code as GdkPixbuf. Returns None if qrcode not available."""
    try:
        import qrcode
        from qrcode.image.pil import PilImage
    except ImportError:
        try:
            import qrcode

            qr = qrcode.QRCode(version=1, box_size=8, border=2)
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            tmp = os.path.join(tempfile.gettempdir(), "emergency_qr.png")
            img.save(tmp)
            return GdkPixbuf.Pixbuf.new_from_file_at_scale(tmp, size, size, True)
        except Exception:
            return None

    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    tmp = os.path.join(tempfile.gettempdir(), "emergency_qr.png")
    img.save(tmp)
    return GdkPixbuf.Pixbuf.new_from_file_at_scale(tmp, size, size, True)


def build_qr_text(data):
    """Build compact text for QR code."""
    lines = ["NODKORT / EMERGENCY CARD"]
    if data["namn"]:
        lines.append(f"Namn: {data['namn']}")
    if data["personnummer"]:
        lines.append(f"PNr: {data['personnummer']}")
    if data["diagnoser"]:
        lines.append(f"Diagnoser: {data['diagnoser']}")
    if data["mediciner"]:
        lines.append(f"Mediciner: {data['mediciner']}")
    if data["allergier"]:
        lines.append(f"Allergier: {data['allergier']}")
    if data["kommunikation"]:
        lines.append(f"Komm.behov: {data['kommunikation']}")
    for k in data.get("kontakter", []):
        if k.get("namn") and k.get("telefon"):
            lines.append(f"Kontakt: {k['namn']} ({k.get('relation', '')}) {k['telefon']}")
    return "\n".join(lines)


class EmergencyCardApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.data = load_data()

    def do_activate(self):
        win = Adw.ApplicationWindow(application=self, title=_("Nodkort"))
        win.set_default_size(420, 700)

        # Main layout with view stack
        self.stack = Adw.ViewStack()
        self.stack.set_vhomogeneous(False)

        # --- VIEW PAGE ---
        view_page = self._build_view_page()
        self.stack.add_titled(view_page, "view", "Nodkort")

        # --- EDIT PAGE ---
        edit_page = self._build_edit_page()
        self.stack.add_titled(edit_page, "edit", "Redigera")

        # --- QR PAGE ---
        qr_page = self._build_qr_page()
        self.stack.add_titled(qr_page, "qr", "QR-kod")

        # Header with view switcher
        header = Adw.HeaderBar()
        switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(switcher)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(header)
        toolbar.set_content(self.stack)

        win.set_content(toolbar)
        win.present()

        # Load CSS for emergency styling
        self._load_css()

    def _load_css(self):
        css = b"""
        .emergency-title {
            font-size: 28px;
            font-weight: bold;
            color: @error_color;
        }
        .emergency-label {
            font-size: 18px;
            font-weight: bold;
        }
        .emergency-value {
            font-size: 17px;
        }
        .emergency-warning {
            font-size: 16px;
            font-weight: bold;
            padding: 12px;
            background: alpha(@error_color, 0.15);
            border-radius: 8px;
        }
        .emergency-section {
            font-size: 20px;
            font-weight: bold;
            color: @accent_color;
        }
        .contact-box {
            padding: 10px;
            border-radius: 8px;
            background: alpha(@accent_color, 0.08);
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_view_page(self):
        scroll = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        # Title
        title = Gtk.Label(label=_("NODKORT"), halign=Gtk.Align.CENTER)
        title.add_css_class("emergency-title")
        box.append(title)

        subtitle = Gtk.Label(label=_("EMERGENCY CARD"), halign=Gtk.Align.CENTER)
        subtitle.set_opacity(0.7)
        box.append(subtitle)

        box.append(Gtk.Separator())

        self.view_labels = {}

        # Personal info fields
        fields = [
            ("namn", _("Name")),
            ("personnummer", "Personnummer"),
            ("diagnoser", "Diagnoser"),
            ("mediciner", "Mediciner"),
            ("allergier", "Allergier"),
        ]
        for key, label_text in fields:
            lbl = Gtk.Label(label=label_text, halign=Gtk.Align.START)
            lbl.add_css_class("emergency-label")
            box.append(lbl)
            val = Gtk.Label(
                label=self.data.get(key, "") or "(ej ifyllt)",
                halign=Gtk.Align.START,
                wrap=True,
                wrap_mode=Pango.WrapMode.WORD_CHAR,
            )
            val.add_css_class("emergency-value")
            val.set_selectable(True)
            self.view_labels[key] = val
            box.append(val)
            box.append(Gtk.Separator())

        # Communication needs - highlighted
        if self.data.get("kommunikation"):
            comm_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            comm_title = Gtk.Label(label=_("KOMMUNIKATIONSBEHOV"), halign=Gtk.Align.START)
            comm_title.add_css_class("emergency-label")
            comm_box.append(comm_title)
            comm_val = Gtk.Label(
                label=self.data["kommunikation"],
                halign=Gtk.Align.START,
                wrap=True,
                wrap_mode=Pango.WrapMode.WORD_CHAR,
            )
            comm_val.add_css_class("emergency-warning")
            comm_box.append(comm_val)
            self.view_labels["kommunikation"] = comm_val
            box.append(comm_box)
            box.append(Gtk.Separator())
        else:
            lbl = Gtk.Label(label=_(_("Kommunikationsbehov")), halign=Gtk.Align.START)
            lbl.add_css_class("emergency-label")
            box.append(lbl)
            val = Gtk.Label(label=_("(ej ifyllt)"), halign=Gtk.Align.START)
            val.add_css_class("emergency-value")
            self.view_labels["kommunikation"] = val
            box.append(val)
            box.append(Gtk.Separator())

        # Contacts
        contacts_title = Gtk.Label(label=_("Kontaktpersoner"), halign=Gtk.Align.START)
        contacts_title.add_css_class("emergency-section")
        box.append(contacts_title)

        self.view_contacts_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._refresh_view_contacts()
        box.append(self.view_contacts_box)

        # Notes
        if self.data.get("anteckningar"):
            box.append(Gtk.Separator())
            lbl = Gtk.Label(label=_("Notes"), halign=Gtk.Align.START)
            lbl.add_css_class("emergency-label")
            box.append(lbl)
            val = Gtk.Label(
                label=self.data["anteckningar"],
                halign=Gtk.Align.START,
                wrap=True,
                wrap_mode=Pango.WrapMode.WORD_CHAR,
            )
            val.add_css_class("emergency-value")
            self.view_labels["anteckningar"] = val
            box.append(val)

        scroll.set_child(box)
        return scroll

    def _refresh_view_contacts(self):
        child = self.view_contacts_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.view_contacts_box.remove(child)
            child = next_child

        for k in self.data.get("kontakter", []):
            if not k.get("namn") and not k.get("telefon"):
                continue
            cbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            cbox.add_css_class("contact-box")
            name_line = f"{k.get('namn', '')} ({k.get('relation', '')})" if k.get("relation") else k.get("namn", "")
            n = Gtk.Label(label=name_line, halign=Gtk.Align.START)
            n.add_css_class("emergency-label")
            cbox.append(n)
            t = Gtk.Label(label=k.get("telefon", ""), halign=Gtk.Align.START, selectable=True)
            t.add_css_class("emergency-value")
            cbox.append(t)
            self.view_contacts_box.append(cbox)

    def _build_edit_page(self):
        scroll = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        self.entries = {}

        fields = [
            ("namn", _("Name"), "Ditt fullstandiga namn"),
            ("personnummer", "Personnummer", "YYYYMMDD-XXXX"),
            ("diagnoser", "Diagnoser", "T.ex. diabetes, epilepsi, autism"),
            ("mediciner", "Mediciner", "T.ex. Insulin 20E, Lamotrigin 200mg"),
            ("allergier", "Allergier", "T.ex. penicillin, notter"),
            ("kommunikation", _("Kommunikationsbehov"), "T.ex. behover extra tid, icke-verbal"),
            ("anteckningar", _("Notes"), "Ovrig viktig information"),
        ]

        for key, label_text, placeholder in fields:
            lbl = Gtk.Label(label=label_text, halign=Gtk.Align.START)
            lbl.add_css_class("emergency-label")
            box.append(lbl)
            entry = Gtk.Entry(
                text=self.data.get(key, ""),
                placeholder_text=placeholder,
                hexpand=True,
            )
            entry.connect("changed", self._on_field_changed, key)
            self.entries[key] = entry
            box.append(entry)

        # Contacts section
        box.append(Gtk.Separator())
        contacts_header = Gtk.Box(spacing=8)
        contacts_title = Gtk.Label(label=_("Kontaktpersoner"), halign=Gtk.Align.START, hexpand=True)
        contacts_title.add_css_class("emergency-section")
        contacts_header.append(contacts_title)
        add_btn = Gtk.Button(label="+ Lagg till")
        add_btn.connect("clicked", self._on_add_contact)
        contacts_header.append(add_btn)
        box.append(contacts_header)

        self.contacts_edit_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._rebuild_contact_entries()
        box.append(self.contacts_edit_box)

        # Save button
        box.append(Gtk.Separator())
        save_btn = Gtk.Button(label="Spara")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        box.append(save_btn)

        scroll.set_child(box)
        return scroll

    def _rebuild_contact_entries(self):
        child = self.contacts_edit_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.contacts_edit_box.remove(child)
            child = next_child

        self.contact_entries = []
        for i, k in enumerate(self.data.get("kontakter", [])):
            frame = Gtk.Frame()
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            inner.set_margin_top(8)
            inner.set_margin_bottom(8)
            inner.set_margin_start(8)
            inner.set_margin_end(8)

            row1 = Gtk.Box(spacing=8)
            name_entry = Gtk.Entry(text=k.get("namn", ""), placeholder_text=_("Name"), hexpand=True)
            rel_entry = Gtk.Entry(text=k.get("relation", ""), placeholder_text="Relation")
            rel_entry.set_size_request(120, -1)
            row1.append(name_entry)
            row1.append(rel_entry)
            inner.append(row1)

            row2 = Gtk.Box(spacing=8)
            phone_entry = Gtk.Entry(text=k.get("telefon", ""), placeholder_text="Telefonnummer", hexpand=True)
            phone_entry.set_input_purpose(Gtk.InputPurpose.PHONE)
            remove_btn = Gtk.Button(label="Ta bort")
            remove_btn.add_css_class("destructive-action")
            remove_btn.connect("clicked", self._on_remove_contact, i)
            row2.append(phone_entry)
            row2.append(remove_btn)
            inner.append(row2)

            frame.set_child(inner)
            self.contacts_edit_box.append(frame)
            self.contact_entries.append({"namn": name_entry, "telefon": phone_entry, "relation": rel_entry})

    def _on_field_changed(self, entry, key):
        self.data[key] = entry.get_text()

    def _on_add_contact(self, btn):
        self.data["kontakter"].append({"namn": "", "telefon": "", "relation": ""})
        self._rebuild_contact_entries()

    def _on_remove_contact(self, btn, index):
        if len(self.data["kontakter"]) > 1:
            self.data["kontakter"].pop(index)
            self._rebuild_contact_entries()

    def _on_save(self, btn):
        # Collect contact data from entries
        contacts = []
        for ce in self.contact_entries:
            contacts.append({
                "namn": ce["namn"].get_text(),
                "telefon": ce["telefon"].get_text(),
                "relation": ce["relation"].get_text(),
            })
        self.data["kontakter"] = contacts
        save_data(self.data)

        # Refresh view page and QR
        self._refresh_view_page()
        self._refresh_qr()

        # Show toast
        toast = Adw.Toast(title="Sparat!")
        toast.set_timeout(2)
        # Find the toast overlay or just save silently
        # We saved successfully - the button flash is enough feedback

    def _refresh_view_page(self):
        for key, label in self.view_labels.items():
            val = self.data.get(key, "") or "(ej ifyllt)"
            label.set_label(val)
        self._refresh_view_contacts()

    def _build_qr_page(self):
        scroll = Gtk.ScrolledWindow(vexpand=True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, halign=Gtk.Align.CENTER)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(16)
        box.set_margin_end(16)

        title = Gtk.Label(label="QR-kod for sjukvardspersonal")
        title.add_css_class("emergency-section")
        box.append(title)

        desc = Gtk.Label(
            label="Visa denna QR-kod for ambulanspersonal\neller sjukvard sa kan de skanna din info.",
            halign=Gtk.Align.CENTER,
            wrap=True,
        )
        box.append(desc)

        self.qr_image = Gtk.Image()
        self.qr_image.set_size_request(300, 300)
        box.append(self.qr_image)

        self.qr_status = Gtk.Label(label="")
        box.append(self.qr_status)

        refresh_btn = Gtk.Button(label="Uppdatera QR-kod")
        refresh_btn.connect("clicked", lambda b: self._refresh_qr())
        box.append(refresh_btn)

        scroll.set_child(box)

        # Generate initial QR
        GLib.idle_add(self._refresh_qr)

        return scroll

    def _refresh_qr(self):
        text = build_qr_text(self.data)
        if not text.strip() or text.strip() == "NODKORT / EMERGENCY CARD":
            self.qr_status.set_label("Fyll i dina uppgifter forst under 'Redigera'.")
            return

        pixbuf = generate_qr_pixbuf(text)
        if pixbuf:
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.qr_image.set_from_paintable(texture)
            self.qr_status.set_label("")
        else:
            self.qr_status.set_label(
                "QR-kod ej tillganglig.\nInstallera: pip install qrcode pillow"
            )


def main():
    app = EmergencyCardApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
