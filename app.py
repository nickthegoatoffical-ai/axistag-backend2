import os
import random
import requests

from flask import Flask, jsonify, request


# ============================================================
# CONFIG
# ============================================================

class GameInfo:
    def __init__(self):
        # PlayFab Title ID
        self.TitleId = "1CB79"

        # IMPORTANT:
        # Put your newly rotated credentials in environment variables.
        self.SecretKey = os.getenv("PLAYFAB_SECRET_KEY", "EY5EY31WC5FSFEJZTZUOEBRAC7CW5JM1QODYUP8D7UHU8UKNWT")
        self.ApiKey = os.getenv("META_API_KEY", "OC|1509567288898275|029faf1d5ac456588312007b779b4340")
        self.DiscordWebhookUrl = os.getenv("DISCORD_WEBHOOK_URL", "")

        # Website
        self.WebsiteUrl = "https://axistag.vercel.app/"

    def get_auth_headers(self):
        return {
            "Content-Type": "application/json",
            "X-SecretKey": self.SecretKey
        }


settings = GameInfo()

app = Flask(__name__)


# ============================================================
# HELPERS
# ============================================================

def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.headers.get(
        "X-Real-IP",
        request.remote_addr or "Unknown"
    )


def get_json():
    data = request.get_json(silent=True)

    if isinstance(data, dict):
        return data

    return {}


def playfab_url(endpoint):
    return (
        f"https://{settings.TitleId}"
        f".playfabapi.com/{endpoint}"
    )


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/", methods=["GET", "POST"])
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Axis Tag Backend</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;

            display: flex;
            align-items: center;
            justify-content: center;

            background: #0b0b0b;
            color: white;

            font-family:
                Arial,
                Helvetica,
                sans-serif;

            text-align: center;
        }

        .container {
            padding: 50px;

            background: #121212;

            border: 1px solid #292929;
            border-radius: 20px;

            box-shadow:
                0 0 40px
                rgba(0, 255, 100, 0.08);
        }

        h1 {
            margin: 0 0 18px;

            color: #00ff66;

            font-size: 42px;
            font-weight: 700;
        }

        p {
            margin: 8px 0;

            color: #aaa;

            font-size: 18px;
        }

        .author {
            color: #00c8ff;

            font-weight: bold;
        }

        .online {
            color: #00ff66;

            font-weight: bold;
        }
    </style>
</head>

<body>

    <div class="container">

        <h1>
            BACKEND IS RUNNING
        </h1>

        <p class="online">
            ● ONLINE
        </p>

        <p class="author">
            MADE BY UNBORN 
        </p>

    </div>

</body>
</html>
"""


# ============================================================
# STATUS
# ============================================================

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "status": "BACKEND IS RUNNING",
        "online": True,
        "author": "UNBORN",
        "titleId": settings.TitleId,
        "website": settings.WebsiteUrl
    }), 200


# ============================================================
# META / OCULUS
# ============================================================

def GetOrgScopedId(oculus_id):
    if not settings.ApiKey:
        return None

    if not oculus_id:
        return None

    try:
        response = requests.get(
            f"https://graph.oculus.com/{oculus_id}",
            params={
                "access_token": settings.ApiKey,
                "fields": "org_scoped_id"
            },
            headers={
                "Content-Type": "application/json"
            },
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get(
                "org_scoped_id"
            )

    except requests.RequestException as error:
        print(
            "GetOrgScopedId error:",
            error
        )

    return None


def GetMetaAlias(oculus_id):
    if not settings.ApiKey:
        return None

    if not oculus_id:
        return None

    try:
        response = requests.get(
            f"https://graph.oculus.com/{oculus_id}",
            params={
                "access_token": settings.ApiKey,
                "fields": "alias"
            },
            headers={
                "Content-Type": "application/json"
            },
            timeout=10
        )

        if response.status_code == 200:
            return response.json().get(
                "alias"
            )

    except requests.RequestException as error:
        print(
            "GetMetaAlias error:",
            error
        )

    return None


def GetIsNonceValid(nonce, oculus_id):
    if not settings.ApiKey:
        return False

    if not nonce or not oculus_id:
        return False

    try:
        response = requests.post(
            "https://graph.oculus.com/user_nonce_validate",
            params={
                "nonce": nonce,
                "user_id": oculus_id,
                "access_token": settings.ApiKey
            },
            headers={
                "Content-Type": "application/json"
            },
            timeout=10
        )

        if response.status_code == 200:
            return bool(
                response.json().get(
                    "is_valid"
                )
            )

    except requests.RequestException as error:
        print(
            "Nonce validation error:",
            error
        )

    return False


# ============================================================
# DISCORD AUTH LOGGING
# ============================================================

def send_auth_webhook(
    success,
    player_ip,
    custom_id=None,
    playfab_id=None,
    oculus_id=None,
    meta_alias=None,
    error_message=None
):
    if not settings.DiscordWebhookUrl:
        return

    try:
        if success:
            title = "AUTHENTICATION SUCCESS"
            color = 65280
        else:
            title = "AUTHENTICATION FAILED"
            color = 16711680

        payload = {
            "embeds": [
                {
                    "title": title,
                    "color": color,

                    "fields": [
                        {
                            "name": "Authentication",
                            "value": (
                                "```ini\n"
                                f"[ IP ]: "
                                f"{player_ip}\n"

                                f"[ Custom ID ]: "
                                f"{custom_id or 'N/A'}\n"

                                f"[ PlayFab ID ]: "
                                f"{playfab_id or 'N/A'}\n"

                                f"[ Oculus ID ]: "
                                f"{oculus_id or 'N/A'}\n"

                                f"[ Meta Alias ]: "
                                f"{meta_alias or 'N/A'}\n"

                                f"[ Error ]: "
                                f"{error_message or 'None'}\n"

                                "```"
                            )
                        }
                    ],

                    "footer": {
                        "text":
                            "Axis Tag Backend"
                    }
                }
            ]
        }

        requests.post(
            settings.DiscordWebhookUrl,
            json=payload,
            timeout=5
        )

    except requests.RequestException as error:
        print(
            "Discord webhook error:",
            error
        )


# ============================================================
# PLAYFAB AUTHENTICATION
# ============================================================

@app.route(
    "/api/PlayFabAuthentication",
    methods=["POST"]
)
def playfab_authentication():

    data = get_json()

    client_ip = get_client_ip()

    required_fields = [
        "Nonce",
        "AppId",
        "Platform",
        "OculusId"
    ]

    missing_fields = [
        field
        for field in required_fields
        if not data.get(field)
    ]

    if missing_fields:

        message = (
            "Missing parameter(s): "
            + ", ".join(missing_fields)
        )

        send_auth_webhook(
            False,
            client_ip,
            custom_id=data.get(
                "CustomId"
            ),
            error_message=message
        )

        return jsonify({
            "Message": message,
            "Error":
                "BadRequest-MissingParameter"
        }), 400

    # Check Title ID
    if data.get("AppId") != settings.TitleId:

        send_auth_webhook(
            False,
            client_ip,
            custom_id=data.get(
                "CustomId"
            ),
            oculus_id=data.get(
                "OculusId"
            ),
            error_message="App ID mismatch"
        )

        return jsonify({
            "Message":
                "Request sent for the wrong App ID",

            "Error":
                "BadRequest-AppIdMismatch"
        }), 400

    oculus_id = data.get(
        "OculusId"
    )

    # --------------------------------------------------------
    # Oculus / Meta verification
    # --------------------------------------------------------

    org_scoped_id = GetOrgScopedId(
        oculus_id
    )

    if not org_scoped_id:

        send_auth_webhook(
            False,
            client_ip,
            custom_id=data.get(
                "CustomId"
            ),
            oculus_id=oculus_id,
            error_message=
                "Oculus verification failed"
        )

        return jsonify({
            "Message":
                "Invalid Oculus ID",

            "Error":
                "BadRequest-InvalidOculusId"
        }), 400

    meta_alias = GetMetaAlias(
        oculus_id
    )

    if not meta_alias:

        send_auth_webhook(
            False,
            client_ip,
            custom_id=data.get(
                "CustomId"
            ),
            oculus_id=oculus_id,
            error_message=
                "Meta alias verification failed"
        )

        return jsonify({
            "Message":
                "Invalid Meta alias",

            "Error":
                "BadRequest-InvalidMetaAlias"
        }), 400

    # --------------------------------------------------------
    # Nonce verification
    # --------------------------------------------------------

    nonce = data.get(
        "Nonce"
    )

    if not GetIsNonceValid(
        nonce,
        oculus_id
    ):

        send_auth_webhook(
            False,
            client_ip,
            custom_id=data.get(
                "CustomId"
            ),
            oculus_id=oculus_id,
            meta_alias=meta_alias,
            error_message=
                "Invalid authentication nonce"
        )

        return jsonify({
            "Message":
                "Invalid authentication nonce",

            "Error":
                "BadRequest-InvalidNonce"
        }), 401

    # --------------------------------------------------------
    # PlayFab login
    # --------------------------------------------------------

    try:

        login_response = requests.post(
            playfab_url(
                "Server/LoginWithServerCustomId"
            ),

            json={
                "ServerCustomId":
                    "OCULUS" +
                    str(oculus_id),

                "CreateAccount":
                    True
            },

            headers=
                settings.get_auth_headers(),

            timeout=15
        )

        # ----------------------------------------------------
        # Successful login
        # ----------------------------------------------------

        if login_response.status_code == 200:

            result = login_response.json().get(
                "data",
                {}
            )

            playfab_id = result.get(
                "PlayFabId"
            )

            session_ticket = result.get(
                "SessionTicket"
            )

            entity_data = result.get(
                "EntityToken",
                {}
            )

            entity_token = entity_data.get(
                "EntityToken"
            )

            entity = entity_data.get(
                "Entity",
                {}
            )

            entity_id = entity.get(
                "Id"
            )

            entity_type = entity.get(
                "Type"
            )

            custom_id = data.get(
                "CustomId"
            )

            # Link Custom ID
            if custom_id:

                requests.post(
                    playfab_url(
                        "Server/LinkServerCustomId"
                    ),

                    json={
                        "ForceLink":
                            True,

                        "PlayFabId":
                            playfab_id,

                        "ServerCustomId":
                            custom_id
                    },

                    headers=
                        settings.get_auth_headers(),

                    timeout=15
                )

            send_auth_webhook(
                True,
                client_ip,
                custom_id=custom_id,
                playfab_id=playfab_id,
                oculus_id=oculus_id,
                meta_alias=meta_alias
            )

            return jsonify({

                "PlayFabId":
                    playfab_id,

                "SessionTicket":
                    session_ticket,

                "EntityToken":
                    entity_token,

                "EntityId":
                    entity_id,

                "EntityType":
                    entity_type

            }), 200

        # ----------------------------------------------------
        # PlayFab error
        # ----------------------------------------------------

        try:
            error_data = (
                login_response.json()
            )
        except ValueError:
            error_data = {}

        error_message = error_data.get(
            "errorMessage",
            "PlayFab authentication failed."
        )

        send_auth_webhook(
            False,
            client_ip,
            custom_id=data.get(
                "CustomId"
            ),
            oculus_id=oculus_id,
            meta_alias=meta_alias,
            error_message=error_message
        )

        return jsonify({

            "Error":
                "PlayFab Error",

            "Message":
                error_message

        }), login_response.status_code

    except requests.RequestException as error:

        print(
            "PlayFab authentication error:",
            error
        )

        return jsonify({

            "Error":
                "BackendError",

            "Message":
                "Unable to contact PlayFab"

        }), 502


# ============================================================
# CACHE PLAYFAB ID
# ============================================================

@app.route(
    "/api/CachePlayFabId",
    methods=["POST"]
)
def cache_playfab_id():

    return jsonify({
        "Message": "Success"
    }), 200


# ============================================================
# TITLE DATA
# ============================================================

@app.route(
    "/api/TitleData",
    methods=["GET", "POST"]
)
def titledata():

    return jsonify({

        "AutoMuteCheckedHours": {
            "hours": 169
        },

        "AutoName_Adverbs": [
            "Cool",
            "Fine",
            "Bald",
            "Bold",
            "Half",
            "Only",
            "Calm",
            "Fab",
            "Ice",
            "Mad",
            "Rad",
            "Big",
            "New",
            "Old",
            "Shy"
        ],

        "AutoName_Nouns": [
            "Gorilla",
            "Chicken",
            "Darling",
            "Sloth",
            "King",
            "Queen",
            "Royal",
            "Major",
            "Actor",
            "Agent",
            "Elder",
            "Honey",
            "Nurse",
            "Doctor",
            "Rebel",
            "Shape",
            "Ally",
            "Driver",
            "Deputy"
        ],

        "CreditsData": [

            {
                "Title":
                    "<color=red>OWNER</color>",

                "Entries": [
                    "UNBORN"
                ]
            },

            {
                "Title":
                    "<color=yellow>CREDITS</color>",

                "Entries": [
                    "UNBORN"
                ]
            }

        ],

        "BundleBoardSign":
            "<color=#ff4141>"
            "AXIS TAG"
            "</color>",

        "BundleKioskButton":
            "<color=#ff4141>"
            "AXIS TAG"
            "</color>",

        "BundleKioskSign":
            "<color=#ff4141>"
            "AXIS TAG"
            "</color>",

        "BundleLargeSign":
            "<color=#ff4141>"
            "AXIS TAG"
            "</color>",

        "EmptyFlashbackText":
            "FLOOR TWO NOW OPEN\n"
            "FOR BUSINESS",

        "EnableCustomAuthentication":
            True,

        "GorillanalyticsChance":
            4320,

        "LatestPrivacyPolicyVersion":
            "2024.09.20",

        "LatestTOSVersion":
            "2024.09.20",

        "MOTD":
            "<color=red>[ WELCOME TO AXIS TAG! ]</color>\n"
"<color=red>WELCOME TUFF GAME!</color>\n"
"<color=blue>https://axistag.vercel.app/</color>\n"
"<color=yellow>JOIN OUR DISCORD!</color>\n"
"<color=purple>https://discord.gg/BZhzeWz2nP</color>\n"
"<color=blue>UNBORN IS THE OWNER</color>\n"
"<color=orange>IM NOT A SKID SO IM USING MY OWN BACKEND</color>",

        "SeasonalStoreBoardSign":
            "<color=yellow>"
            "AXIS TAG"
            "</color>",

        "TOS_2024.09.20":
            "https://axistag.vercel.app/",

        "TOBAlreadyOwnCompTxt":
            "AXIS TAG",

        "TOBAlreadyOwnPurchaseBundle":
            "AXIS TAG",

        "TOBDefCompTxt":
            "AXIS TAG",

        "TOBDefPurchaseBtnDefTxt":
            "AXIS TAG",

        "UseLegacyIAP":
            False

    }), 200


# ============================================================
# OCULUS IAP
# ============================================================

@app.route(
    "/api/ConsumeOculusIAP",
    methods=["POST"]
)
def consume_oculus_iap():

    data = get_json()

    nonce = data.get(
        "nonce"
    )

    user_id = data.get(
        "userID"
    )

    sku = data.get(
        "sku"
    )

    if not nonce or not user_id or not sku:

        return jsonify({
            "error": True,
            "message":
                "Missing parameters"
        }), 400

    if not settings.ApiKey:

        return jsonify({
            "error": True,
            "message":
                "Meta API key not configured"
        }), 500

    try:

        response = requests.post(
            "https://graph.oculus.com/"
            "consume_entitlement",

            params={
                "nonce":
                    nonce,

                "user_id":
                    user_id,

                "sku":
                    sku,

                "access_token":
                    settings.ApiKey
            },

            headers={
                "Content-Type":
                    "application/json"
            },

            timeout=15
        )

        result = response.json()

        if result.get(
            "success"
        ):

            return jsonify({
                "result": True
            }), 200

        return jsonify({
            "error": True
        }), 400

    except requests.RequestException as error:

        print(
            "Oculus IAP error:",
            error
        )

        return jsonify({
            "error": True,
            "message":
                "Meta request failed"
        }), 502


# ============================================================
# AGREEMENTS
# ============================================================

@app.route(
    "/api/GetAcceptedAgreements",
    methods=["GET", "POST"]
)
def get_accepted_agreements():

    return jsonify({

        "PrivacyPolicy":
            "1.1.28",

        "TOS":
            "11.05.22.2"

    }), 200


@app.route(
    "/api/SubmitAcceptedAgreements",
    methods=["GET", "POST"]
)
def submit_accepted_agreements():

    return jsonify({}), 200


# ============================================================
# CODE ITEM
# ============================================================

@app.route(
    "/api/ConsumeCodeItem",
    methods=["POST"]
)
def consume_code_item():

    data = get_json()

    code = data.get(
        "itemGUID"
    )

    playfab_id = data.get(
        "playFabID"
    )

    session_ticket = data.get(
        "playFabSessionTicket"
    )

    if not code:
        return jsonify({
            "error":
                "Missing itemGUID"
        }), 400

    if not playfab_id:
        return jsonify({
            "error":
                "Missing playFabID"
        }), 400

    if not session_ticket:
        return jsonify({
            "error":
                "Missing playFabSessionTicket"
        }), 400

    # Add your private code database here.
    # Do not put redeemable codes in public files.

    return jsonify({
        "result":
            "CodeInvalid"
    }), 404


# ============================================================
# RANDOM NAME
# ============================================================

@app.route(
    "/api/v2/GetName",
    methods=["GET", "POST"]
)
def get_name():

    return jsonify({
        "result":
            f"GORILLA"
            f"{random.randint(1000, 9999)}"
    }), 200


# ============================================================
# PHOTON AUTH
# ============================================================

@app.route(
    "/api/photon",
    methods=["GET", "POST"]
)
def photon_auth():

    data = get_json()

    ticket = data.get(
        "Ticket"
    )

    nonce = data.get(
        "Nonce"
    )

    platform = data.get(
        "Platform"
    )

    if not ticket:

        return jsonify({

            "resultCode":
                2,

            "message":
                "Invalid token",

            "userId":
                None,

            "nickname":
                None

        }), 400

    user_id = ticket.split("-")[0]

    if (
        not user_id
        or len(user_id) != 16
    ):

        return jsonify({

            "resultCode":
                2,

            "message":
                "Invalid token",

            "userId":
                None,

            "nickname":
                None

        }), 400

    if (
        platform
        and platform != "Quest"
    ):

        return jsonify({

            "Error":
                "Bad request",

            "Message":
                "Invalid platform!"

        }), 403

    if not nonce:

        return jsonify({

            "Error":
                "Bad request",

            "Message":
                "Not Authenticated!"

        }), 401

    try:

        response = requests.post(

            playfab_url(
                "Server/"
                "GetUserAccountInfo"
            ),

            json={
                "PlayFabId":
                    user_id
            },

            headers=
                settings.get_auth_headers(),

            timeout=15
        )

        if response.status_code == 200:

            account_info = (
                response
                .json()
                .get(
                    "UserInfo",
                    {}
                )
                .get(
                    "UserAccountInfo",
                    {}
                )
            )

            nickname = account_info.get(
                "Username"
            )

            return jsonify({

                "resultCode":
                    1,

                "message":
                    "Authenticated user "
                    f"{user_id.lower()} "
                    "title "
                    f"{settings.TitleId.lower()}",

                "userId":
                    user_id.upper(),

                "nickname":
                    nickname

            }), 200

        return jsonify({

            "resultCode":
                0,

            "message":
                "Something went wrong",

            "userId":
                None,

            "nickname":
                None

        }), 500

    except requests.RequestException as error:

        print(
            "Photon error:",
            error
        )

        return jsonify({

            "resultCode":
                0,

            "message":
                "Backend connection failed",

            "userId":
                None,

            "nickname":
                None

        }), 502


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "error":
            "Not Found",

        "message":
            "Endpoint does not exist"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({
        "error":
            "Method Not Allowed"
    }), 405


@app.errorhandler(500)
def internal_error(error):

    return jsonify({
        "error":
            "Internal Server Error"
    }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "9080"
        )
    )

    print(
        "======================================"
    )

    print(
        "       AXIS TAG"
    )

    print(
        "======================================"
    )

    print(
        "STATUS: BACKEND IS RUNNING"
    )

    print(
        "MADE BY: UNBORN"
    )

    print(
        "TITLE ID: 1CB79"
    )

    print(
        "WEBSITE: "
        "https://axistag.vercel.app/"
    )

    print(
        f"PORT: {port}"
    )

    print(
        "======================================"
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
