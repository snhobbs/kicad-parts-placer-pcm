import logging
import os
import wx
import wx.aui
import wx.lib.buttons as buttons
from pathlib import Path
import pcbnew
import sys
import pandas as pd


sys.path.append(Path(__file__).parent.absolute().as_posix())

import kicad_parts_placer_

_log = logging.getLogger("kicad_partsplacer-pcm")
_log.setLevel(logging.DEBUG)

_board = None

def set_board(board):
    global _board
    _board = board

def get_board():
    return _board

class Settings:
    """
    All the options that can be passed
    """

    def __init__(self):
        self.use_aux_origin: bool = False
        self.group_name = "parts placer"
        self.mirror=False
        self.group=False


class Meta:
    toolname = "kicadpartsplacer"
    title = "Test Point Report"
    body = """
    """
    about_text = ""
    short_description = "Parts Placer"
    frame_title = ""
    website = "https://www.thejigsapp.com"
    version = "0.1.9"


class SuccessPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        # Static text for success message
        success_text = "Submission successful!"
        success_label = wx.StaticText(self, label=success_text)

        # Sizer for layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(success_label, 0, wx.ALL, 5)
        self.SetSizer(sizer)


def setattr_keywords(obj, name, value):
    return setattr(obj, name, value)


class MyPanel(wx.Panel):
    def __init__(self, parent):
        _log.debug("MyPanel.__init__")
        super().__init__(parent)
        self.settings = Settings()

        # Get current working directory
        dir_ = Path(os.getcwd())
        if pcbnew.GetBoard():
            set_board(pcbnew.GetBoard())

        if get_board():
            wd = Path(get_board().GetFileName()).absolute()
            if wd.exists():
                dir_ = wd.parent
        default_file_path = dir_ / f"{Meta.toolname}-report.csv"
        default_board_file_path = dir_ / f"{Meta.toolname}.kicad_pcb"

        file_label = wx.StaticText(self, label="File Input:")
        self.file_selector = wx.FilePickerCtrl(
            self,
            style=wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL,
            wildcard="CSV files (*.csv)|*.csv",
            path=default_file_path.as_posix(),
        )
        self.file_selector.SetPath(default_file_path.as_posix())

        file_output_label = wx.StaticText(self, label="File Output:")
        self.file_output_selector = wx.FilePickerCtrl(
            self,
            style=wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL,
            wildcard="KiCAD PCB (*.kicad_pcb)|*.kicad_pcb",
            path=default_board_file_path.as_posix(),
        )
        self.file_output_selector.SetPath(default_board_file_path.as_posix())

        # Lorem Ipsum text
        lorem_text = wx.StaticText(self, label=Meta.body)

        # Buttons
        self.submit_button = buttons.GenButton(self, label="Submit")
        self.cancel_button = buttons.GenButton(self, label="Cancel")
        self.submit_button.SetBackgroundColour(wx.Colour(150, 225, 150))
        self.cancel_button.SetBackgroundColour(wx.Colour(225, 150, 150))
        self.submit_button.Bind(wx.EVT_BUTTON, self.on_submit)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        # Horizontal box sizer for buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.submit_button, 0, wx.ALL | wx.EXPAND, 5)
        button_sizer.Add(self.cancel_button, 0, wx.ALL, 5)

        # Origin selectiondd
        self.use_aux_origin_cb = wx.CheckBox(self, label="Use drill/place file origin")
        self.use_aux_origin_cb.SetValue(True)
        self.settings.use_aux_origin = self.use_aux_origin_cb.GetValue()

        # Group
        self.group_parts_cb = wx.CheckBox(self, label="Group Parts")
        self.group_parts_cb.SetValue(True)
        self.settings.group = self.group_parts_cb.GetValue()

        self.Bind(wx.EVT_CHECKBOX, self.on_checkbox_toggle)

        # Sizer for layout
        # sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.use_aux_origin_cb, 0, wx.ALL, 10)
        sizer.Add(self.group_parts_cb, 0, wx.ALL, 10)

        sizer.Add(file_label, 0, wx.ALL, 5)
        sizer.Add(self.file_selector, 0, wx.EXPAND | wx.ALL, 5)

        sizer.Add(file_output_label, 0, wx.ALL, 5)
        sizer.Add(self.file_output_selector, 0, wx.EXPAND | wx.ALL, 5)

        sizer.Add(lorem_text, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.SetSizer(sizer)
        # self.SetSizeHints(1000,1000)
        # self.SetMinSize((1000, 1000))  # Set a minimum width and height for the frame
        self.Layout()

    def on_checkbox_toggle(self, event):
        self.settings.use_aux_origin = self.use_aux_origin_cb.GetValue()
        self.settings.group = self.group_parts_cb.GetValue()
        _log.debug(self.settings.use_aux_origin)
        _log.debug(self.settings.group)

    def on_submit(self, event):
        file_path = Path(self.file_selector.GetPath())
        output_file_path = Path(self.file_output_selector.GetPath())
        if file_path and output_file_path:
            print("Submitting...")
            print("File Path:", file_path)

            board = get_board()
            origin = (0,0)
            if self.settings.use_aux_origin:
                ds = board.GetDesignSettings()
                origin = pcbnew.ToMM(ds.GetAuxOrigin())

            pcbnew.SaveBoard(output_file_path.as_posix(), board)
            board = pcbnew.LoadBoard(output_file_path.as_posix())
            components_df = pd.read_csv(file_path)
            print(components_df)

            board_out = kicad_parts_placer_.place_parts(
                board,
                components_df = components_df,
                origin=origin)

            group_name = self.settings.group_name
            if self.settings.group:
                _log.debug("GROUPING PARTS")
                board = kicad_parts_placer_.group_parts(board, components_df, group_name=group_name)

            pcbnew.SaveBoard(output_file_path.as_posix(), board_out)

            self.GetTopLevelParent().EndModal(wx.ID_OK)
            # self.GetParent().ShowSuccessPanel()
        else:
            wx.MessageBox(
                "Please select an input and output file.", "Error", wx.OK | wx.ICON_ERROR
            )

    def on_cancel(self, event):
        print("Canceling...")
        self.GetTopLevelParent().EndModal(wx.ID_CANCEL)


class AboutPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        font = wx.Font(
            12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
        bold = wx.Font(
            10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD
        )

        # Static text for about information
        message_text = wx.StaticText(self, label=Meta.about_text)
        version_text = wx.StaticText(self, label=f"Version: {Meta.version}")

        pre_link_text = wx.StaticText(self, label="For more information visit: ")
        from wx.lib.agw.hyperlink import HyperLinkCtrl

        link = HyperLinkCtrl(self, wx.ID_ANY, f"{Meta.website}", URL=Meta.website)

        link.SetColours(wx.BLUE, wx.BLUE, wx.BLUE)
        version_text.SetFont(bold)
        message_text.SetFont(font)
        pre_link_text.SetFont(font)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(version_text, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(message_text, 1, wx.EXPAND | wx.ALL, 5)

        link_sizer = wx.BoxSizer(wx.HORIZONTAL)
        link_sizer.Add(pre_link_text, 0, wx.EXPAND, 0)
        link_sizer.Add(link, 0, wx.EXPAND, 0)
        sizer.Add(link_sizer, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)


class MyDialog(wx.Dialog):
    def __init__(self, parent, title):
        super().__init__(
            parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        # Create a notebook with two tabs
        notebook = wx.Notebook(self)
        tab_panel = MyPanel(notebook)
        about_panel = AboutPanel(notebook)
        self.success_panel = SuccessPanel(notebook)

        notebook.AddPage(tab_panel, "Main")
        notebook.AddPage(about_panel, "About")

        # Sizer for layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(sizer)
        self.SetSizeHints(500, 500)  # Set minimum size hints

    def on_close(self, event):
        self.EndModal(wx.ID_CANCEL)
        event.Skip()

    def ShowSuccessPanel(self):
        self.GetSizer().GetChildren()[0].GetWindow().Destroy()
        self.GetSizer().Insert(0, self.success_panel)
        self.Layout()

    def on_maximize(self, event):
        self.fit_to_screen()

    def on_size(self, event):
        if self.IsMaximized():
            self.fit_to_screen()

    def fit_to_screen(self):
        screen_width, screen_height = wx.DisplaySize()
        self.SetSize(wx.Size(screen_width, screen_height))


class Plugin(pcbnew.ActionPlugin):
    def __init__(self):
        super().__init__()

        _log.debug("Loading kicad_partsplacer")

        self.logger = None
        self.config_file = None

        self.name = Meta.title
        self.category = "Read PCB"
        self.pcbnew_icon_support = hasattr(self, "show_toolbar_button")
        self.show_toolbar_button = True
        icon_dir = Path(__file__).parent
        self.icon_file_name = (icon_dir / "icon.png").as_posix()
        self.description = Meta.body

    def Run(self):
        dlg = MyDialog(None, title=Meta.title)
        try:
            dlg.ShowModal()

        except Exception as e:
            _log.error(e)
            raise
        finally:
            _log.debug("Destroy Dialog")
            dlg.Destroy()


if __name__ == "__main__":
    logging.basicConfig()
    _log.setLevel(logging.DEBUG)
    import sys
    if len(sys.argv) > 1:
        set_board(pcbnew.LoadBoard(sys.argv[1]))
    app = wx.App()
    p = Plugin()
    p.Run()
