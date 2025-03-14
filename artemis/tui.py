#!/usr/bin/env 
from typing import Optional, List
import asyncio
import argparse
from os import path, mkdir, W_OK, access
import yaml
import bcrypt
import secrets
import string
from sqlalchemy.engine import Row

from core.data import Data
from core.config import CoreConfig

try:
    from asciimatics.widgets import Frame, Layout, Text, Button, RadioButtons, CheckBox, Divider, Label
    from asciimatics.scene import Scene
    from asciimatics.screen import Screen
    from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
except:
    print("Artemis TUI requires asciimatics, please install it using pip")
    exit(1)


class State:   
    class SelectedUser:
        def __init__(self, id: Optional[int] = None, name: Optional[str] = None):
            self.id = id
            self.name = name

        def __str__(self):
            if self.id is not None:
                return f"{self.name} ({self.id})" if self.name else f"User{self.id:04d}"
            return "None"

        def __int__(self):
            return self.id if self.id else 0

    class SelectedCard:
        def __init__(self, id: Optional[int] = None, access_code: Optional[str] = None):
            self.id = id
            self.access_code = access_code
        
        def __str__(self):
            if self.id is not None and self.access_code:
                return f"{self.access_code} ({self.id})"
            return "None"

        def __int__(self):
            return self.id if self.id else 0

    class SelectedArcade:
        def __init__(self, id: Optional[int] = None, country: Optional[str] = None, name: Optional[str] = None):
            self.id = id
            self.country = country
            self.name = name
        
        def __str__(self):
            if self.id is not None:
                return f"{self.name} ({self.country}{self.id:05d})" if self.name else f"{self.country}{self.id:05d}"
            return "None"
        
        def __int__(self):
            return self.id if self.id else 0

    class SelectedMachine:
        def __init__(self, id: Optional[int] = None, serial: Optional[str] = None):
            self.id = id
            self.serial = serial
        
        def __str__(self):
            if self.id is not None:
                return f"{self.serial} ({self.id})"
            return "None"
        
        def __int__(self):
            return self.id if self.id else 0

    def __init__(self):
        self.selected_user: self.SelectedUser = self.SelectedUser()
        self.selected_card: self.SelectedCard = self.SelectedCard()
        self.selected_arcade: self.SelectedArcade = self.SelectedArcade()
        self.selected_machine: self.SelectedMachine = self.SelectedMachine()
        self.last_err: str = ""
        self.search_results: List[Row] = []
        self.search_type: str = ""

    def set_user(self, id: int, username: Optional[str]) -> None:
        self.selected_user = self.SelectedUser(id, username)

    def clear_user(self) -> None:
        self.selected_user = self.SelectedUser()

    def set_card(self, id: int, access_code: Optional[str]) -> None:
        self.selected_card = self.SelectedCard(id, access_code)

    def clear_card(self) -> None:
        self.selected_card = self.SelectedCard()

    def set_arcade(self, id: int, country: str = "JPN", name: Optional[str] = None) -> None:
        self.selected_arcade = self.SelectedArcade(id, country, name)

    def clear_arcade(self) -> None:
        self.selected_arcade = self.SelectedArcade()

    def set_machine(self, id: int, serial: Optional[str]) -> None:
        self.selected_machine = self.SelectedMachine(id, serial)

    def clear_machine(self) -> None:
        self.selected_machine = self.SelectedMachine()

    def set_last_err(self, err: str) -> None:
        self.last_err = err

    def clear_last_err(self) -> None:
        self.last_err = ""
    
    def clear_search_results(self) -> None:
        self.search_results = []

state = State()
data: Data = None
loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()

class MainView(Frame):
    def __init__(self, screen: Screen):
        super(MainView, self).__init__(
            screen, 
            screen.height * 2 // 3, 
            screen.width * 2 // 3, 
            hover_focus=True, 
            can_scroll=False, 
            title="ARTEMiS TUI"
        )

        layout = Layout([100], True)
        self.add_layout(layout)
        layout.add_widget(Button("User Management", self._user_mgmt))
        layout.add_widget(Button("Card Management", self._card_mgmt))
        layout.add_widget(Button("Arcade Management", self._arcade_mgmt))
        layout.add_widget(Button("Machine Management", self._mech_mgmt))
        layout.add_widget(Button("Quit", self._quit))
        
        self.fix()
    
    def _user_mgmt(self):
        self.save()
        raise NextScene("User Management")
    
    def _card_mgmt(self):
        self.save()
        raise NextScene("Card Management")
    
    def _arcade_mgmt(self):
        self.save()
        raise NextScene("Arcade Management")
    
    def _mech_mgmt(self):
        self.save()
        raise NextScene("Mech Management")
    
    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")

class ManageUser(Frame):
    def __init__(self, screen: Screen):
        super(ManageUser, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="User Management",
            on_load=self._redraw
        )

        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Create User", self._create_user))
        layout.add_widget(Button("Lookup User", self._lookup))
    
    def _redraw(self):
        self._layouts = [self._layouts[0]]
        
        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Edit User", self._edit_user, disabled=state.selected_user.id == 0 or state.selected_user.id is None))
        layout.add_widget(Button("Delete User", self._del_user, disabled=state.selected_user.id == 0 or state.selected_user.id is None))
        layout.add_widget((Divider()))
        
        usr_cards = []
        if state.selected_user.id != 0:
            cards = loop.run_until_complete(data.card.get_user_cards(state.selected_user.id))
            for card in cards:
                usr_cards.append(card._asdict())

        if len(usr_cards) > 0:
            layout3 = Layout([100], True)
            self.add_layout(layout3)
            
            card_status = "Available"
            if card['is_locked'] and card['is_banned']:
                card_status = "Locked and Banned"
            if card['is_locked']:
                card_status = "Locked"
            if card['is_banned']:
                card_status = "Banned"

            layout3.add_widget(RadioButtons(
                [(f"{card['id']} | {card['access_code']} | {card_status} | {card['memo'] if card['memo'] else '-'}", state.SelectedCard(card['id'], card['access_code'])) for card in usr_cards],
                "Cards:",
                "usr_cards"
            ))
            layout3.add_widget(Button('Select Card', self._sel_card))
            layout3.add_widget(Divider())

        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        a = Text("", f"status", readonly=True, disabled=True)
        a.value = f"Selected User: {state.selected_user}"
        layout2.add_widget(a)
        layout2.add_widget(Button("Back", self._back), 2)
        
        self.fix()
    
    def _sel_card(self):
        self.save()
        a = self.data.get('usr_cards')
        state.set_card(a.id, a.access_code)
        raise NextScene("Card Management")
    
    def _create_user(self):
        self.save()
        raise NextScene("Create User")
    
    def _lookup(self):
        self.save()
        raise NextScene("Lookup User")
    
    def _edit_user(self):
        self.save()
        raise NextScene("Edit User")
    
    def _del_user(self):
        self.save()
        raise NextScene("Delete User")

    def _back(self):
        self.save()
        raise NextScene("Main")

class ManageCard(Frame):
    def __init__(self, screen: Screen):
        super(ManageCard, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Card Management",
            on_load=self._redraw
        )

        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Create Card", self._create_card))
        layout.add_widget(Button("Lookup Card", self._lookup))
    
    def _redraw(self):
        self._layouts = [self._layouts[0]]
        
        layout = Layout([3])
        self.add_layout(layout)
        layout.add_widget(Button("Edit Card", self._edit_card, disabled=state.selected_card.id == 0 or state.selected_card.id is None))
        layout.add_widget(Button("Reassign Card", self._edit_card, disabled=state.selected_card.id == 0 or state.selected_card.id is None))
        layout.add_widget(Button("Delete Card", self._del_card, disabled=state.selected_card.id == 0 or state.selected_card.id is None))
        layout.add_widget((Divider()))

        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        a = Text("", f"status", readonly=True, disabled=True)
        a.value = f"Selected Card: {state.selected_card}"
        layout2.add_widget(a)
        layout2.add_widget(Button("Back", self._back), 2)
        
        self.fix()
    
    def _create_card(self):
        self.save()
        raise NextScene("Create Card")
    
    def _lookup(self):
        self.save()
        raise NextScene("Lookup Card")
    
    def _edit_card(self):
        self.save()
        raise NextScene("Edit Card")
    
    def _del_card(self):
        self.save()
        raise NextScene("Delete Card")

    def _back(self):
        self.save()
        raise NextScene("Main")

class CreateUserView(Frame):
    def __init__(self, screen: Screen):
        super(CreateUserView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Create User"
        )

        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Text("Username:", "username"))
        layout.add_widget(Text("Email:", "email"))
        layout.add_widget(Text("Password:", "passwd"))
        layout.add_widget(CheckBox("", "Add Card:", "is_add_card", ))
        layout.add_widget(RadioButtons([
            ("User", "1"),
            ("User Manager", "2"),
            ("Arcde Manager", "4"),
            ("Sysadmin", "8"),
            ("Owner", "255"),
        ], "Role:", "role"))

        layout3 = Layout([100])
        self.add_layout(layout3)
        layout3.add_widget(Text("", f"status", readonly=True, disabled=True))
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        
        self.fix()

    def _ok(self):
        self.save()
        if not self.data.get("username"):
            state.set_last_err("Username cannot be blank")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return

        state.clear_last_err()
        self.find_widget('status').value = state.last_err

        if not self.data.get("passwd"):
            pw = "".join(
                secrets.choice(string.ascii_letters + string.digits) for i in range(20)
            )
        else:
            pw = self.data.get("passwd")
        
        hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

        loop.run_until_complete(self._create_user_async(self.data.get("username"), hash.decode(), self.data.get("email"), self.data.get('role')))

        raise NextScene("User Management")
    
    async def _create_user_async(self, username: str, password: str, email: Optional[str], role: str):
        usr_id = await data.user.create_user(
            username=username,
            email=email if email else None,
            password=password,
            permission=int(role)
        )

        state.set_user(usr_id, username)

    def _cancel(self):
        state.clear_last_err()
        self.find_widget('status').value = state.last_err
        raise NextScene("User Management")

class SearchResultsView(Frame):
    def __init__(self, screen: Screen):
        super(SearchResultsView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Search Results",
            on_load=self._redraw
        )
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Select", self._select_current), 2)
        layout2.add_widget(Button("Cancel", self._cancel), 2)
    
    def _redraw(self):
        self._layouts = [self._layouts[0]]
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        opts = []
        if state.search_type == "user":
            layout.add_widget(Label("      ID   | Username |   Role   | Email"))
            layout.add_widget(Divider())
            
            for usr in state.search_results:
                name = str(usr['username'])
                if len(name) < 8:
                    name = str(usr['username']) + ' ' * (8 - len(name))
                elif len(name) > 8:
                    name = usr['username'][:5] + "..."
                
                opts.append((f"{usr['id']:05d} | {name} | {usr['permissions']:08b} | {usr['email']}", state.SelectedUser(usr["id"], str(usr['username']))))
            
        layout.add_widget(RadioButtons(opts, "", "selopt"))
        
        self.fix()

    def _select_current(self):
        self.save()
        a = self.data.get('selopt')
        state.set_user(a.id, a.name)
        raise NextScene("User Management")

    def _cancel(self):
        state.clear_last_err()
        raise NextScene("User Management")

class LookupUserView(Frame):
    def __init__(self, screen):
        super(LookupUserView, self).__init__(
            screen,
            screen.height * 2 // 3,
            screen.width * 2 // 3,
            hover_focus=True,
            can_scroll=False,
            title="Lookup User"
        )
        
        layout = Layout([1, 1], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(RadioButtons([
            ("Username", "1"),
            ("Email", "2"),
            ("Access Code", "3"),
            ("User ID", "4"),
        ], "Search By:", "search_type"))
        layout.add_widget(Text("Search:", "search_str"), 1)

        layout3 = Layout([100])
        self.add_layout(layout3)
        layout3.add_widget(Text("", f"status", readonly=True, disabled=True))
        
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Search", self._lookup), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        
        self.fix()
    
    def _lookup(self):
        self.save()
        if not self.data.get("search_str"):
            state.set_last_err("Search cannot be blank")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return
        
        state.clear_last_err()
        self.find_widget('status').value = state.last_err

        search_type = self.data.get("search_type")
        if search_type == "1":
            loop.run_until_complete(self._lookup_user_by_username(self.data.get("search_str")))
        elif search_type == "2":
            loop.run_until_complete(self._lookup_user_by_email(self.data.get("search_str")))
        elif search_type == "3":
            loop.run_until_complete(self._lookup_user_by_access_code(self.data.get("search_str")))
        elif search_type == "4":
            loop.run_until_complete(self._lookup_user_by_id(self.data.get("search_str")))
        else:
            state.set_last_err("Unknown search type")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return

        if len(state.search_results) < 1:
            state.set_last_err("Search returned no results")
            self.find_widget('status').value = state.last_err
            self.screen.reset()
            return
        
        state.search_type = "user"
        raise NextScene("Search Results")

    async def _lookup_user_by_id(self, user_id: str):
        usr = await data.user.get_user(user_id)

        if usr is not None:
            state.search_results = [usr]

    async def _lookup_user_by_username(self, username: str):
        usr = await data.user.find_user_by_username(username)

        if usr is not None:
            state.search_results = usr

    async def _lookup_user_by_email(self, email: str):
        usr = await data.user.find_user_by_email(email)

        if usr is not None:
            state.search_results = usr

    async def _lookup_user_by_access_code(self, access_code: str):
        card = await data.card.get_card_by_access_code(access_code)

        if card is not None:
            usr = await data.user.get_user(card['user'])
            if usr is not None:
                state.search_results = [usr]

    def _cancel(self):
        state.clear_last_err()
        self.find_widget('status').value = state.last_err
        raise NextScene("User Management")

def demo(screen:Screen, scene: Scene):
    scenes = [
        Scene([MainView(screen)], -1, name="Main"),
        Scene([ManageUser(screen)], -1, name="User Management"),
        Scene([CreateUserView(screen)], -1, name="Create User"),
        Scene([LookupUserView(screen)], -1, name="Lookup User"),
        Scene([SearchResultsView(screen)], -1, name="Search Results"),
        Scene([ManageCard(screen)], -1, name="Card Management"),
    ]

    screen.play(scenes, stop_on_resize=False, start_scene=scene, allow_int=True)

last_scene = None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Database utilities")
    parser.add_argument(
        "--config", "-c", type=str, help="Config folder to use", default="config"
    )
    args = parser.parse_args()
    
    cfg = CoreConfig()
    if path.exists(f"{args.config}/core.yaml"):
        cfg_dict = yaml.safe_load(open(f"{args.config}/core.yaml"))
        cfg_dict.get("database", {})["loglevel"] = "info"
        cfg.update(cfg_dict)

    if not path.exists(cfg.server.log_dir):
        mkdir(cfg.server.log_dir)

    if not access(cfg.server.log_dir, W_OK):
        print(
            f"Log directory {cfg.server.log_dir} NOT writable, please check permissions"
        )
        exit(1)

    data = Data(cfg)

    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=True, arguments=[last_scene])
            exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene
