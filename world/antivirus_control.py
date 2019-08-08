from evennia.utils import search

def debug(msg):
    search.objects("loki")[0].msg(msg)

def antivirus():
    return search.objects("dn8bossfight#antivirus")[0]

def start(caller):
    text = "You are looking at the AntiVirus Control Console"

    options = (
        {"desc": "Scan", "goto": "scan"},
        {"desc": "Update", "goto": "update"},
        {"desc": "Logging", "goto": "logging"},
        {"desc": "Configuration", "goto": "adjust_antibodies"},
    )

    return text, options

def _reply(caller, raw_input, **kwargs):
    msg = kwargs["msg"]
    caller.msg("|r"+msg)
    return None

def scan(caller):
    text = "Launch some AntiBodies"
    options = (
        {"desc": "Run a Full System Scan", "goto": (_reply, {"msg":"A quarantine operation is already in progress"})},
        {"desc": "Run a Targeted Scan", "goto": (_reply, {"msg":"A quarantine operation is already in progress"})},
        {"desc": "Return to main menu", "goto": "start"},
    )
    return text, options
def update(caller):
    text = "Update the AntiVirus Engine"
    options = (
        {"desc": "Update AntiBody Definitions", "goto": (_reply, {"msg":"Administrator privileges required"})},
        {"desc": "Update Program Definitions (Requires Reboot)", "goto": (_reply, {"msg":"Update AntiBody Definitions"})},
        {"desc": "Return to main menu", "goto": "start"},
    )
    return text, options
def logging(caller):
    text = ""
    options = (
        {"desc": "Log Settings", "goto": "log_settings"},
        {"desc": "View Logs", "goto": (_reply, {"msg":"Insufficient privileges"})},
        {"desc": "Return to main menu", "goto": "start"},
    )
    return text, options
def log_settings(caller):
    text = "Launch some AntiBodies"
    options = (
        {"desc": "Full Logging (requires 100GB of free space)", "goto": (_reply, {"msg":"Insufficient free space"})},
        {"desc": "Limited Logging", "goto": (_reply, {"msg":"Logging already enabled"})},
        {"desc": "Log rotation", "goto": (_reply, {"msg":"Logs rotate daily"})},
        {"desc": "Return to logging menu", "goto": "logging"},
    )
    return text, options

def adjust_antibodies(caller):
    text = "Adjust the AntiBody configuration"

    def enabled(value):
        if value:
            return "|genabled"
        else:
            return "|rdisabled"

    options = (
        {
            "desc": "Toggle Basic AntiBodies (%s)" % enabled(antivirus().db.base_antibody_enabled),
            "goto": (_safe_toggle_antivirus_config, {"config": "base_antibody_enabled"})
        },    
        {
            "desc": "Toggle Horizontally Polarized AntiBodies (%s)" % enabled(antivirus().db.xfirst_antibody_enabled),
            "goto": (_safe_toggle_antivirus_config, {"config": "xfirst_antibody_enabled"})
        },
        {
            "desc": "Toggle Vertically Polarized AntiBodies (%s)" % enabled(antivirus().db.yfirst_antibody_enabled),
            "goto": (_safe_toggle_antivirus_config, {"config": "yfirst_antibody_enabled"})
        },
        {
            "desc": "Toggle Smart AntiBodies (%s)" % enabled(antivirus().db.wrand_antibody_enabled),
            "goto": (_safe_toggle_antivirus_config, {"config": "wrand_antibody_enabled"})
        },
        {
            "desc": "Return to main menu",
            "goto": "start",
        },
    )

    return text, options

def _safe_toggle_antivirus_config(caller, rawstring, **kwargs):
    config = kwargs["config"]

    debug("toggling av config: %s"%(config))
    all_configs = [
        "xfirst_antibody_enabled",
        "yfirst_antibody_enabled",
        "base_antibody_enabled",
        "wrand_antibody_enabled",
    ]
    avroom = antivirus()
    num_enabled = len([True for prop in all_configs if avroom.attributes.get(prop)])

    if avroom.attributes.get(config) and num_enabled == 1:
        caller.msg("\n\n|r  !!!! Failsafe: unable to disable all antibodies !!!!  \n\n")
    else:
        antivirus().attributes.add(config, not antivirus().attributes.get(config))
        debug("antivirus config updated: %s => %s"%(config, antivirus().attributes.get(config)))
        
    return None