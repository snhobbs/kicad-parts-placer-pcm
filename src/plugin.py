import logging
import os
import sys
import csv
from pathlib import Path
import wx
import wx.aui
from wx.lib import buttons
import pcbnew

"""x: posx, positionx, xpos, xposition, midx, xmid, x
y: posy, positiony, ypos, yposition, midy, ymid, y
rotation: rot, angle, rotate, rotation,
side: layer, side,
ref des: designator, reference designator, ref, ref des"""


path_ = Path(__file__).parent.absolute()
sys.path.append(str(path_))

from dataframe_lite_ import DataFrame
import kicad_parts_placer_
import _version

_log = logging.getLogger("kicad_partsplacer-pcm")
_log.setLevel(logging.DEBUG)

_board = None
_frame_size = (800, 600)
_frame_size_min = (500, 300)


def read_csv(fname: str, **kwargs):
    """
    Basic CSV reading to dataframe
    """
    with open(fname, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, **kwargs)
        return DataFrame(list(reader))


def set_board(board):
    """
    Sets the board global.
    """
    global _board
    _board = board


def get_board():
    """
    Use instead of pcbnew.GetBoard to allow
    command line use.
    """
    return _board


class Settings:
    """
    All the options that can be passed
    """

    def __init__(self):
        self.use_aux_origin: bool = False
        self.group_name = "parts placer"
        self.mirror = False
        self.group = False


class Meta:
    """
    Information about package
    """

    toolname = "kicadpartsplacer"
    title = "Parts Placer"
    body = (
        "Flip, mirror, move, rotate, and move components based off inputs from a spreadsheet. \
Enforce a form-factor, keep mechanical placements under version control, and allow \
updating of a templated design. Easily enforce grids or maintain test point patterns."
    )
    about_text = "Declaratively place components using a spreadsheet"
    frame_title = "Parts Placer"
    short_description = "Parts Placer"
    website = "https://www.thejigsapp.com"
    gitlink = "https://github.com/snhobbs/kicad-parts-placer-pcm"
    version = _version.__version__


def setattr_keywords(obj, name, value):
    return setattr(obj, name, value)


class MyPanel(wx.Panel):
    """
    Primary panel
    """

    def __init__(self, parent):
        _log.info("MyPanel.__init__")
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

        file_output_label = wx.StaticText(self, label="File Backup:")
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

    def on_checkbox_toggle(self, _):
        self.settings.use_aux_origin = self.use_aux_origin_cb.GetValue()
        self.settings.group = self.group_parts_cb.GetValue()
        _log.debug(self.settings.use_aux_origin)
        _log.debug(self.settings.group)

    def on_submit(self, _):
        file_path = Path(self.file_selector.GetPath())
        output_file_path = Path(self.file_output_selector.GetPath())

        if not file_path or not output_file_path:
            wx.MessageBox(
                "Please select an input and output file.",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        print("Submitting...")
        print("File Path:", file_path)

        board = get_board()
        if not board:
            wx.MessageBox(
                "No board found",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        origin = (0, 0)
        if self.settings.use_aux_origin:
            ds = board.GetDesignSettings()
            origin = pcbnew.ToMM(ds.GetAuxOrigin())

        _log.debug("Save Board")
        pcbnew.SaveBoard(str(output_file_path), board)

        if not file_path.exists():
            wx.MessageBox(
                "Spreadsheet not found",
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        components_df = read_csv(file_path)
        components_df.columns = kicad_parts_placer_.translate_header(
            components_df.columns
        )
        components_df = kicad_parts_placer_.setup_dataframe(components_df)
        for field in ["x", "y", "rotation"]:
            if field not in components_df.columns:
                continue
            components_df[field] = [float(pt) for pt in components_df[field]]

        valid, errors = kicad_parts_placer_.check_input_valid(components_df)
        if len(errors):
            msg = f"{'\n'.join(errors)}\n{', '.join(components_df.columns)}"
            wx.MessageBox(
                msg,
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            return

        board = kicad_parts_placer_.place_parts(
            board, components_df=components_df, origin=origin
        )

        group_name = self.settings.group_name
        if self.settings.group:
            _log.debug("GROUPING PARTS")
            board = kicad_parts_placer_.group_parts(
                board, components_df, group_name=group_name
            )

        wx.MessageBox(
            f"Moved: {len(components_df)}\nBackup PCB: {str(output_file_path)}",
            "Success",
            wx.OK,
        )

        self.GetTopLevelParent().EndModal(wx.ID_OK)
        # self.GetTopLevelParent().EndModal(wx.ID_CANCEL)
        return

    def on_cancel(self, _):
        print("Canceling...")
        self.GetTopLevelParent().EndModal(wx.ID_CANCEL)


class AboutPanel(wx.Panel):
    """
    About panel tab
    """

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
        body_text = wx.StaticText(self, label=Meta.body)
        input_header_text = wx.StaticText(self, label="Input Format:")
        input_header_body_text = wx.StaticText(
            self, label="Note: White space and character case ignored"
        )

        list_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES)
        list_ctrl.InsertColumn(0, "Field", width=150)
        list_ctrl.InsertColumn(1, "Alias", width=500)
        list_ctrl.InsertColumn(2, "Required", width=100)

        for key, value in kicad_parts_placer_._header_pseudonyms.items():
            index = list_ctrl.InsertItem(list_ctrl.GetItemCount(), key)
            list_ctrl.SetItem(index, 1, ", ".join(value))
            list_ctrl.SetItem(
                index, 2, str(key in kicad_parts_placer_._required_columns)
            )

        from wx.lib.agw.hyperlink import HyperLinkCtrl

        pre_link_text = wx.StaticText(self, label="Brought to you by: ")
        link = HyperLinkCtrl(self, wx.ID_ANY, f"{Meta.website}", URL=Meta.website)
        link.SetColours(wx.BLUE, wx.BLUE, wx.BLUE)

        pre_gh_link_text = wx.StaticText(self, label="Git Repo: ")
        gh_link = HyperLinkCtrl(self, wx.ID_ANY, f"{Meta.gitlink}", URL=Meta.gitlink)
        gh_link.SetColours(wx.BLUE, wx.BLUE, wx.BLUE)

        version_text.SetFont(bold)
        body_text.SetFont(font)
        message_text.SetFont(font)
        input_header_text.SetFont(bold)

        pre_link_text.SetFont(font)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(version_text, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(message_text, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(body_text, 2, wx.EXPAND | wx.ALL, 5)
        sizer.Add(input_header_text, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(input_header_body_text, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(list_ctrl, 1, wx.EXPAND, 5)

        link_sizer = wx.BoxSizer(wx.HORIZONTAL)
        link_sizer.Add(pre_link_text, 0, wx.EXPAND, 0)
        link_sizer.Add(link, 0, wx.EXPAND, 0)
        sizer.Add(link_sizer, 1, wx.EXPAND | wx.ALL, 5)

        gh_link_sizer = wx.BoxSizer(wx.HORIZONTAL)
        gh_link_sizer.Add(pre_gh_link_text, 0, wx.EXPAND, 0)
        gh_link_sizer.Add(gh_link, 0, wx.EXPAND, 0)
        sizer.Add(gh_link_sizer, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)


class MyDialog(wx.Dialog):
    """
    Top level GUI view
    """

    def __init__(self, parent, title):
        super().__init__(
            parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        # Create a notebook with two tabs
        notebook = wx.Notebook(self)
        tab_panel = MyPanel(notebook)
        about_panel = AboutPanel(notebook)
        # self.success_panel = SuccessPanel(notebook)

        notebook.AddPage(tab_panel, "Main")
        notebook.AddPage(about_panel, "About")

        # Sizer for layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(sizer)
        self.SetMinSize(_frame_size_min)
        self.SetSize(_frame_size)

    def on_close(self, event):
        self.EndModal(wx.ID_CANCEL)
        event.Skip()

    # def ShowSuccessPanel(self):
    #    self.GetSizer().GetChildren()[0].GetWindow().Destroy()
    #    self.GetSizer().Insert(0, self.success_panel)

    def on_maximize(self, _):
        self.fit_to_screen()

    def on_size(self, _):
        if self.IsMaximized():
            self.fit_to_screen()

    def fit_to_screen(self):
        screen_width, screen_height = wx.DisplaySize()
        self.SetSize(wx.Size(screen_width, screen_height))


class Plugin(pcbnew.ActionPlugin):
    def __init__(self):
        super().__init__()

        _log.debug("Loading kicad_partsplacer")

        self.logger = _log
        self.config_file = None

        self.name = Meta.title
        self.category = "Write PCB"
        self.pcbnew_icon_support = hasattr(self, "show_toolbar_button")
        self.show_toolbar_button = True
        icon_dir = Path(__file__).parent
        self.icon_file_path = icon_dir / "icon.png"
        assert self.icon_file_path.exists()
        self.icon_file_name = str(self.icon_file_path)
        self.description = Meta.body

    def defaults(self):
        pass

    def Run(self):
        pcb_frame = None

        try:
            pcb_frame = [
                x for x in wx.GetTopLevelWindows() if x.GetName() == "PcbFrame"
            ][0]
        except IndexError:
            pass

        dlg = MyDialog(pcb_frame, title=Meta.title)
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

    if len(sys.argv) > 1:
        set_board(pcbnew.LoadBoard(sys.argv[1]))
    app = wx.App()
    p = Plugin()
    p.Run()
