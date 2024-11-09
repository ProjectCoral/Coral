import os
import pickle
import json
import logging
from colorama import Fore
from collections import defaultdict

logger = logging.getLogger(__name__)

class PermSystem:
    register = None
    config = None

    def __init__(self, register, config):
        self.register = register
        self.config = config
        self.perm_file = self.config.get('perm_file', './coral.perms')

        self.register.hook_perm_system(self)
        logger.info("Permission system has been hooked with Register.")

        self.load_user_perms()
        self.registered_perms = {}

        self.register_perm("ALL", "All Permissions")
        self.register_perm("permission_system", "Base Permission")

        self.register.register_command("perms", "perms <show|list>|<add|remove> <perm_name> <user_id> <group_id> - Manages user permissions.", self.strip_command, ["permission_system"])

    
    def strip_command(self, *args):
        command_args = ' '.join(args)
        if not command_args:
            return "Invalid command format.\nUsage:\n perms <show|list>\n perms <add|remove> <perm_name> <user_id> <group_id>"
        try:
            if command_args.strip() == "show":
                return self.show_perms()
            elif command_args.strip() == "list":
                return self.list_perms()
            func, args = command_args.strip().split(" ", 1)
        except ValueError:
            return "Invalid command format."
        if func == "add":
            return self.add_perm(args)
        elif func == "remove":
            return self.remove_perm(args)
        else:
            return f"Invalid command {args}."

    def load_user_perms(self):
        if not os.path.exists(self.perm_file):
            logger.warning(Fore.YELLOW + f"Permission file not found, creating a default one." + Fore.RESET)
            self.user_perms = defaultdict(list)
        else:
            with open(self.perm_file, 'rb') as f:
                self.user_perms = pickle.load(f)

    def save_user_perms(self):
        with open(self.perm_file, 'wb') as f:
            pickle.dump(self.user_perms, f)

    def add_perm(self, command):
        try:
            perm_name, user_id, group_id = command.split(" ", 2)
        except ValueError:
            return "Invalid command format."
        if perm_name not in self.registered_perms:
            return f"Permission {perm_name} not registered."
        if user_id == '-1':  # 修改为字符串
            self.user_perms[str(group_id)].append(perm_name)
        else:
            self.user_perms[str(user_id)].append((perm_name, str(group_id)))
        self.save_user_perms()
        return "Permission added."
    
    def remove_perm(self, command):
        try:
            perm_name, user_id, group_id = command.split(" ", 2)
        except ValueError:
            return "Invalid command format."
        if perm_name not in self.registered_perms:
            return f"Permission {perm_name} not registered."
        try:
            if user_id == '-1':  # 修改为字符串
                self.user_perms[str(group_id)].remove(perm_name)
            else:
                self.user_perms[str(user_id)].remove((perm_name, str(group_id)))
        except ValueError:
            return f"Permission {perm_name} not found for user {user_id} in group {group_id}."
        self.save_user_perms()
        return "Permission removed."

    def check_perm(self, perm_name, user_id, group_id):
        if user_id == 'Console':
            return True
        if isinstance(perm_name, list):
            for p in perm_name:
                if self.check_perm(p, user_id, group_id):
                    return True
            return False
        perm_name = str(perm_name)
        logger.debug(f"Checking permission {perm_name} for user {user_id} in group {group_id}")
        if perm_name not in self.registered_perms:
            logger.warning(Fore.YELLOW + f"Permission {perm_name} not registered, ingoring it." + Fore.RESET)
            return True
        if user_id == '-1':
            if perm_name in self.user_perms[str(group_id)]:
                return True
            return False
        else:
            user_id = str(user_id)
            if user_id not in self.user_perms:
                logger.warning(f"User {user_id} has no permissions registered.")
                return False
            for perm in self.user_perms[user_id]:
                if perm[0] == "ALL":
                    return True
                if perm[0] == perm_name:
                    if perm[1] == str(group_id) or perm[1] == 'ALL' or perm[1] == -1:
                        return True
        return False

    
    def register_perm(self, perm_name, perm_desc):
        self.registered_perms[perm_name] = perm_desc

    def show_perms(self, *args):
        message = "Total registered " + str(len(self.registered_perms)) + " Permissions.\n"
        message += "Available Permissions:\n"
        for perm_name, perm_desc in self.registered_perms.items():
            message += f"{perm_name}: {perm_desc}\n"
        message += "\nFor more information about user permissions, use the 'perms list' command.\n"
        return message

    def list_perms(self, *args):
        message = "User Permissions:\n"
        for user, perms in self.user_perms.items():
            if user == '-1':
                message += f"Group {user}: "
                for perm in perms:
                    message += f"  {perm}\n"
                continue
            message += f"User {user}:\n"
            for perm in perms:
                if isinstance(perm, str):
                    message += f"  {perm}\n"
                else:
                    message += f"  {perm[0]} in group {perm[1]}\n"
        return str(message)