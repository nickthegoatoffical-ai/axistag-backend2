# || backend also made by loaded (ugh i hate python) credits to xre for some parts ||

import base64
import os
import hashlib
import hmac
import json
import logging
import random
import secrets
import time
import uuid
from datetime import date, datetime

from flask import Flask, Response, jsonify, request
import requests

app = Flask(__name__)


VOTING_WEBHOOK            = "https://discord.com/api/webhooks/1570555339252961572/fkdmLnatrFfIbjz3ACfH6svGUIAGG5wwiGUKa6SqwMvCOB45n7hTf1RdZHUPgDBUJFsn"
BAD_NONCE_WEBHOOK         = "https://discord.com/api/webhooks/1570555339252961572/fkdmLnatrFfIbjz3ACfH6svGUIAGG5wwiGUKa6SqwMvCOB45n7hTf1RdZHUPgDBUJFsn"
GOOD_NONCE_WEBHOOK        = "https://discord.com/api/webhooks/1570555339252961572/fkdmLnatrFfIbjz3ACfH6svGUIAGG5wwiGUKa6SqwMvCOB45n7hTf1RdZHUPgDBUJFsn"
DISCORD_WEBHOOK_URL       = "https://discord.com/api/webhooks/1570555339252961572/fkdmLnatrFfIbjz3ACfH6svGUIAGG5wwiGUKa6SqwMvCOB45n7hTf1RdZHUPgDBUJFsn"
failedAttestation_webhook = "https://discord.com/api/webhooks/1570555339252961572/fkdmLnatrFfIbjz3ACfH6svGUIAGG5wwiGUKa6SqwMvCOB45n7hTf1RdZHUPgDBUJFsn"
successAttestation_webhook = "https://discord.com/api/webhooks/1570555339252961572/fkdmLnatrFfIbjz3ACfH6svGUIAGG5wwiGUKa6SqwMvCOB45n7hTf1RdZHUPgDBUJFsn"
failedorgscope_webhook     = "https://discord.com/api/webhooks/1570555339252961572/fkdmLnatrFfIbjz3ACfH6svGUIAGG5wwiGUKa6SqwMvCOB45n7hTf1RdZHUPgDBUJFsn"
successOrgscope_webhook    = "https://discord.com/api/webhooks/1570555339252961572/fkdmLnatrFfIbjz3ACfH6svGUIAGG5wwiGUKa6SqwMvCOB45n7hTf1RdZHUPgDBUJFsn"
attestNonceLogs_webhook    = "https://discord.com/api/webhooks/1570555339252961572/fkdmLnatrFfIbjz3ACfH6svGUIAGG5wwiGUKa6SqwMvCOB45n7hTf1RdZHUPgDBUJFsn"

apiKey          = os.environ.get("OCULUS_APP_CREDS", "OC|1374537005750260|e9b87278713b144ef0519abfc7678e78")
bannedHwids     = []
validPackage    = "com.AxisTag"

MINIMUM_APP_VERSION = "0.0.0"
ATTESTATION_SECRET  = os.environ.get("ATTESTATION_SECRET", "ghostisaverysigmauwubakarizzlercakewithaxistagdevs")
ATTESTATION_TTL     = 60


class Info:
    def __init__(self):
        self.TitleId:   str = os.environ.get("TITLE_ID", "1CB79")
        self.SecretKey: str = os.environ.get("PLAYFAB_SECRET", "PZN6SJCDYOP1FY86ZAQM333QUD5CSYTEPXBOO5WOU8A5W4YC55")
        self.AppCreds:   str = os.environ.get("OCULUS_APP_CREDS", "OC|1374537005750260|e9b87278713b144ef0519abfc7678e78")

    def ServerAuthHeaders(self):
        return {"Content-Type": "application/json", "X-SecretKey": self.SecretKey}


settings         = Info()
friend_requests  = {}
friend_usernames = {}
friend_presence  = {}


# ── DISCORD LOGGING HELPER FUNCTIONS ──────────────────────────────────────────

def log_to_discord(message, webhook_url=DISCORD_WEBHOOK_URL):
    if not webhook_url:
        return
    try:
        requests.post(webhook_url, json={"content": message[:2000]}, timeout=5)
    except Exception as e:
        print(f"Discord log failed: {e}")


def failedAttestation(userid, hwid, metauser, orgscopeidd, sha256, packagename, claims):
    embed = {
        "embeds": [
            {
                "title": "User Failed Attestation",
                "color": 3015427,
                "fields": [
                    {"name": "UserId", "value": f"```{userid}```"},
                    {"name": "Hwid", "value": f"```{hwid}```"},
                    {"name": "MetaUser", "value": f"```{metauser}```"},
                    {"name": "OrgScopedID", "value": f"```{orgscopeidd}```"},
                    {"name": "Sha256", "value": f"```{sha256}```"},
                    {"name": "PackageName", "value": f"```{packagename}```"},
                    {"name": "All Claims", "value": f"```{claims}```"}
                ]
            }
        ]
    }
    if failedAttestation_webhook:
        try:
            requests.post(failedAttestation_webhook, json=embed, timeout=5)
        except Exception as e:
            print(f"Failed to post failedAttestation embed: {e}")


def successAttestation(userid, hwid, metauser, orgscopeidd, sha256, packagename, claims):
    embed = {
        "embeds": [
            {
                "title": "User Passed Attestation",
                "color": 16711904,
                "fields": [
                    {"name": "UserId", "value": f"```{userid}```"},
                    {"name": "Hwid", "value": f"```{hwid}```"},
                    {"name": "MetaUser", "value": f"```{metauser}```"},
                    {"name": "OrgScopedID", "value": f"```{orgscopeidd}```"},
                    {"name": "Sha256", "value": f"```{sha256}```"},
                    {"name": "PackageName", "value": f"```{packagename}```"},
                    {"name": "All Claims", "value": f"```{claims}```"}
                ]
            }
        ]
    }
    if successAttestation_webhook:
        try:
            requests.post(successAttestation_webhook, json=embed, timeout=5)
        except Exception as e:
            print(f"Failed to post successAttestation embed: {e}")


def failedOrgscope(userid, alldata):
    embed = {
        "embeds": [
            {
                "title": "User Failed Orgscope Check",
                "color": 13434624,
                "fields": [
                    {"name": "UserId", "value": f"```{userid}```"},
                    {"name": "All Data", "value": f"```{json.dumps(alldata)}```"}
                ]
            }
        ]
    }
    if failedorgscope_webhook:
        try:
            requests.post(failedorgscope_webhook, json=embed, timeout=5)
        except Exception as e:
            print(f"Failed to post failedOrgscope embed: {e}")


def successOrgscope(userid, alldata):
    embed = {
        "embeds": [
            {
                "title": "User Passed Orgscope Check",
                "color": 8716543,
                "fields": [
                    {"name": "UserId", "value": f"```{userid}```"},
                    {"name": "All Data", "value": f"```{json.dumps(alldata)}```"}
                ]
            }
        ]
    }
    if successOrgscope_webhook:
        try:
            requests.post(successOrgscope_webhook, json=embed, timeout=5)
        except Exception as e:
            print(f"Failed to post successOrgscope embed: {e}")


def logAttestationToken(userid, attestNonce, alldata):
    embed = {
        "embeds": [
            {
                "title": "User Passed Orgscope Check",
                "color": 15304105,
                "fields": [
                    {"name": "UserId", "value": f"```{userid}```"},
                    {"name": "Attestation Nonce", "value": f"```{attestNonce}```"},
                    {"name": "All Data", "value": f"```{json.dumps(alldata)}```"}
                ]
            }
        ]
    }
    if attestNonceLogs_webhook:
        try:
            requests.post(attestNonceLogs_webhook, json=embed, timeout=5)
        except Exception as e:
            print(f"Failed to post logAttestationToken embed: {e}")


# ── ATTESTATION SHIT ───────────────────────────────────────────────────────

def b64Decode(val: str) -> str:
    missing_padding = len(val) % 4
    if missing_padding:
        val += '=' * (4 - missing_padding)
    return base64.b64decode(val).decode('utf-8')


def CheckAttestation(token: str):
    url = f"https://graph.oculus.com/platform_integrity/verify?token={token}&access_token={apiKey}"
    try:
        res = requests.get(url, timeout=10)
        json_data = res.json()
        rjson = json_data.get("data", [{}])[0]
        if rjson.get("message") == "success":
            return rjson
        return False
    except Exception:
        return False


def GenToken() -> str:
    length = random.randint(22, 40)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.choice(chars) for _ in range(length))


def CheckOrgscope(orgscope: str):
    url = f"https://graph.oculus.com/{orgscope}?access_token={apiKey}&fields=org_scoped_id,alias"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json()
        return False
    except Exception:
        return False


def GenerateChallengeNonce() -> str:
    length = random.randint(22, 172)
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    randomStr = ''.join(random.choice(chars) for _ in range(length))
    encoded = base64.b64encode(randomStr.encode('utf-8')).decode('utf-8')
    challengeNonce = encoded.replace('+', '-').replace('/', '_').rstrip('=')
    return challengeNonce


# ── PLAYFAB & GENERAL HELPERS ─────────────────────────────────────────────────

def get_username_from_playfab(playfab_id):
    url = f"https://{settings.TitleId}.playfabapi.com/Server/GetUserAccountInfo"
    try:
        resp = requests.post(url, json={"PlayFabId": playfab_id},
                             headers=settings.ServerAuthHeaders(), timeout=5)
        resp.raise_for_status()
        username = (resp.json().get("data", {})
                               .get("UserInfo", {})
                               .get("TitleInfo", {})
                               .get("DisplayName"))
        if username:
            friend_usernames[playfab_id] = username
            return username
    except Exception as e:
        print(f"GetUserAccountInfo error for {playfab_id}: {e}")
    return f"User_{playfab_id}"


def CheckSessionTicket(ticket):
    try:
        url  = f"https://{settings.TitleId}.playfabapi.com/Server/AuthenticateSessionTicket"
        resp = requests.post(url, json={"SessionTicket": ticket},
                             headers=settings.ServerAuthHeaders(), timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def _vtuple(v: str):
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def version_allowed(client_ver: str) -> bool:
    if not client_ver or client_ver.strip() == "":
        return True
    try:
        return _vtuple(client_ver) >= _vtuple(MINIMUM_APP_VERSION)
    except Exception:
        return True


def make_challenge_token(oculus_id: str) -> str:
    ts      = str(int(time.time()))
    id_hash = hashlib.sha256(oculus_id.encode()).hexdigest()[:16]
    payload = f"{ts}.{id_hash}"
    sig     = hmac.new(ATTESTATION_SECRET.encode(), payload.encode(),
                       hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_challenge_token(token: str, oculus_id: str) -> bool:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False
        ts_str, id_hash, provided_sig = parts
        if time.time() - int(ts_str) > ATTESTATION_TTL:
            return False
        expected_hash = hashlib.sha256(oculus_id.encode()).hexdigest()[:16]
        if not hmac.compare_digest(id_hash, expected_hash):
            return False
        payload      = f"{ts_str}.{id_hash}"
        expected_sig = hmac.new(ATTESTATION_SECRET.encode(),
                                payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(provided_sig, expected_sig)
    except Exception:
        return False


def get_bound_hwid(playfab_id: str):
    url = f"https://{settings.TitleId}.playfabapi.com/Server/GetUserData"
    try:
        resp = requests.post(url,
                             json={"PlayFabId": playfab_id, "Keys": ["BoundHWID"]},
                             headers=settings.ServerAuthHeaders(), timeout=5)
        return (resp.json().get("data", {})
                           .get("Data", {})
                           .get("BoundHWID", {})
                           .get("Value"))
    except Exception:
        return None


def set_bound_hwid(playfab_id: str, hwid_hash: str):
    url = f"https://{settings.TitleId}.playfabapi.com/Server/UpdateUserData"
    try:
        requests.post(url,
                      json={"PlayFabId": playfab_id,
                            "Data": {"BoundHWID": hwid_hash},
                            "Permission": "Private"},
                      headers=settings.ServerAuthHeaders(), timeout=5)
    except Exception:
        pass


# ── ATTESTATION ENDPOINTS ─────────────────────────────────────────────────────

@app.route("/v2/player/client/auth/begin/QUEST", methods=["POST"])
def auth_begin_quest():
    body = request.get_json(force=True, silent=True) or {}
    userId = body.get("UserId")

    if not CheckOrgscope(userId):
        failedOrgscope(userId, body)
        return jsonify({"message": "skid lol"}), 401

    successOrgscope(userId, body)

    attesationNonce = GenerateChallengeNonce()
    logAttestationToken(userId, attesationNonce, body)
    return jsonify({"AttestationNonce": attesationNonce}), 201


@app.route("/v2/player/client/auth/complete/QUEST", methods=["POST"])
def auth_complete_quest():
    body = request.get_json(force=True, silent=True) or {}
    userId = body.get("UserId")
    attestationToken = body.get("AttestationToken")
    metaNonce = body.get("MetaNonce")

    CheckAttest = CheckAttestation(attestationToken)
    if not CheckAttest:
        return jsonify({"message": "failed attesation"}), 401

    Claims = CheckAttest.get("claims", "")
    try:
        Decoded = b64Decode(Claims)
        jsonPrs = json.loads(Decoded)

        Expiration = jsonPrs.get("request_details", {}).get("exp")
        TimeStamp = jsonPrs.get("request_details", {}).get("timestamp")

        AppIntegrity = jsonPrs.get("app_state", {}).get("app_integrity_state")
        Sha256 = jsonPrs.get("app_state", {}).get("package_cert_sha256_digest", [None])[0]
        Package = jsonPrs.get("app_state", {}).get("package_id")
        VersionCode = jsonPrs.get("app_state", {}).get("version")

        Hwid = jsonPrs.get("device_state", {}).get("unique_id")
        DeviceIntegrity = jsonPrs.get("device_state", {}).get("device_integrity_state")

        Token = str(GenToken())
        PlayerIda = f"GTAGING-{uuid.uuid4()}"

        Uin = CheckOrgscope(userId) or {}
        MetaUser = Uin.get("alias")
        orgscopeId = Uin.get("org_scoped_id")

        if Hwid in bannedHwids:
            return jsonify({"message": "hwid banned lol"}), 401

        if (AppIntegrity != "StoreRecognized" or
            Package != validPackage or
            DeviceIntegrity != "Advanced"):
            failedAttestation(userId, Hwid, MetaUser, orgscopeId, Sha256, Package, Claims)
            return jsonify({"message": "failed attesation"}), 401

        successAttestation(userId, Hwid, MetaUser, orgscopeId, Sha256, Package, Claims)

        return jsonify({
            "ExternalProviderId": userId,
            "ExternalProviderUsername": MetaUser,
            "IsPrimaryId": True,
            "PlayerId": PlayerIda,
            "Tags": None,
            "Token": Token,
            "ExpirationTime": Expiration
        }), 201

    except Exception as e:
        print(f"Error parsing attestation token: {e}")
        return jsonify({"message": "failed attesation"}), 401


# ── PLAYFAB AUTHENTICATION  ──────────────────────────────────────────────

@app.route("/api/PlayFabAuthentication", methods=["POST", "GET"])
def PlayFabAuthy():
    ua = request.headers.get("User-Agent", "")
    print(f"[Auth] User-Agent: {ua}")

    json_data = request.get_json(force=True, silent=True)
    if json_data is None:
        return jsonify({"Message": "Request body is missing or cannot be parsed.",
                        "Error": "BadRequest-BadBody"}), 400

    print(f"[Auth] Body: {json.dumps(json_data, indent=2)}")

    AppId          = json_data.get("AppId")
    AppVersion     = json_data.get("AppVersion", "")
    Nonce          = json_data.get("Nonce")
    OculusId       = json_data.get("OculusId")
    Platform       = json_data.get("Platform")
    HWID           = json_data.get("HWID", "")
    ChallengeToken = json_data.get("ChallengeToken", "")
    CustomId       = json_data.get("CustomId", "")

    if not version_allowed(AppVersion):
        return jsonify({
            "Error":   "OutdatedClient",
            "Message": f"Version {AppVersion} is no longer supported. "
                       f"Update to {MINIMUM_APP_VERSION} or later."
        }), 426

    for field, val, err in [
        ("AppId",    AppId,    "BadRequest-NoAppId"),
        ("Nonce",    Nonce,    "BadRequest-NoNonce"),
        ("OculusId", OculusId, "BadRequest-NoOculusId"),
        ("Platform", Platform, "BadRequest-NoPlatform"),
    ]:
        if not val:
            return jsonify({"Message": f"Missing {field} parameter", "Error": err}), 400

    if AppId != settings.TitleId:
        return jsonify({"Message": "Wrong AppId parameter",
                        "Error": "BadRequest-WrongAppId"}), 400
    if Platform != "Quest":
        return jsonify({"Message": f"Invalid Platform: {Platform}",
                        "Error": "BadRequest-InvalidPlatform"}), 400

    if ChallengeToken:
        if not verify_challenge_token(ChallengeToken, str(OculusId)):
            print(f"[Auth] BLOCKED bad/expired ChallengeToken. OculusId: {OculusId}")
            return jsonify({"Message": "Invalid or expired attestation token.",
                            "Error": "BadRequest-BadAttestation"}), 403
        print(f"[Auth] ChallengeToken verified for OculusId: {OculusId}")
    else:
        generated = make_challenge_token(str(OculusId))
        if not verify_challenge_token(generated, str(OculusId)):
            return jsonify({"Message": "Attestation subsystem error.",
                            "Error": "Internal-AttestationFault"}), 500
        print(f"[Auth] Inline attestation passed for OculusId: {OculusId}")

    if not CustomId:
        CustomId = f"OCULUSLOCAL{OculusId}"
    print(f"[Auth] CustomId: {CustomId}")

    if GOOD_NONCE_WEBHOOK:
        requests.post(GOOD_NONCE_WEBHOOK, json={"embeds": [{
            "title": "🟢 Valid Login",
            "description": f"```ini\n[Nonce] : {Nonce}\n[CustomId] : {CustomId}```",
            "color": 65280
        }]}, timeout=5)

    print(f"[Auth] Logging into PlayFab with CustomId: {CustomId}")
    login_req = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/LoginWithServerCustomId",
        json={"ServerCustomId": CustomId, "CreateAccount": True},
        headers=settings.ServerAuthHeaders(), timeout=10
    )
    print(f"[Auth] PlayFab login ({login_req.status_code}): "
          f"{json.dumps(login_req.json(), indent=2)}")

    if login_req.status_code != 200:
        if login_req.status_code == 403:
            ban_info = login_req.json()
            if ban_info.get("errorCode") == 1002:
                BanDetails        = ban_info.get("errorDetails", {})
                BanReason         = next(iter(BanDetails.keys()), "You are banned.")
                BanTime           = BanDetails.get(BanReason, [])
                BanExpirationTime = BanTime[0] if BanTime else "NO EXPIRATION TIME PROVIDED."
                return jsonify({"BanMessage": BanReason,
                                "BanExpirationTime": BanExpirationTime}), 403
        print(f"[Auth] Unknown PlayFab error: {login_req.status_code}")
        return jsonify({"Error": "Unknown", "Message": "Something Happened"}), login_req.status_code

    data          = login_req.json().get("data", {})
    SessionTicket = data.get("SessionTicket")
    EntityToken   = data.get("EntityToken", {}).get("EntityToken")
    PlayFabId     = data.get("PlayFabId")
    EntityId      = data.get("EntityToken", {}).get("Entity", {}).get("Id")
    EntityType    = data.get("EntityToken", {}).get("Entity", {}).get("Type")

    if HWID:
        hwid_hash   = hashlib.sha256(HWID.encode()).hexdigest()
        stored_hwid = get_bound_hwid(PlayFabId)

        if stored_hwid is None:
            set_bound_hwid(PlayFabId, hwid_hash)
            print(f"[Auth] HWID bound for {PlayFabId}: {hwid_hash[:12]}…")
        elif not hmac.compare_digest(stored_hwid, hwid_hash):
            print(f"[Auth] HWID MISMATCH for {PlayFabId}")
            log_to_discord(
                f"⚠️ **HWID Mismatch** | `{PlayFabId}` | "
                f"Stored: `{stored_hwid[:16]}…` | Got: `{hwid_hash[:16]}…`"
            )
            return jsonify({
                "BanMessage": "Hardware mismatch detected. Contact support if this is your device.",
                "BanExpirationTime": "Indefinite"
            }), 403
    else:
        print(f"[Auth] No HWID provided, skipping bind check for {PlayFabId}")

    requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Client/LinkCustomID",
        json={"CustomId": CustomId, "ForceLink": True},
        headers={"Content-Type": "application/json", "X-Authorization": SessionTicket}, timeout=10
    )

    ts_req = requests.post(
        url=f"https://{settings.TitleId}.playfabapi.com/Server/GetUserAccountInfo",
        json={"PlayFabId": PlayFabId},
        headers=settings.ServerAuthHeaders(), timeout=10
    )
    AccountCreationIsoTimestamp = (
        ts_req.json().get("data", {}).get("UserInfo", {}).get("Created")
    )

    response_body = {
        "SessionTicket":               SessionTicket,
        "EntityToken":                 EntityToken,
        "PlayFabId":                   PlayFabId,
        "EntityId":                    EntityId,
        "EntityType":                  EntityType,
        "AccountCreationIsoTimestamp": AccountCreationIsoTimestamp
    }
    print(f"[Auth] SUCCESS: {json.dumps(response_body, indent=2)}")
    return jsonify(response_body), 200


# ── REMAINING FLASK ROUTES ────────────────────────────────────────────────────

@app.route("/api/CachePlayFabId", methods=["POST"])
def CachePlayFabId():
    data          = request.get_json() or {}
    PlayFabId     = data.get("PlayFabId", "null")
    SessionTicket = data.get("SessionTicket", "null")
    Platform      = data.get("Platform", "null")

    if not CheckSessionTicket(SessionTicket):
        return jsonify({"Error": "Invalid Session Ticket", "code": 403, "Result": "false"}), 403
    if PlayFabId not in SessionTicket.split("-")[0]:
        return jsonify({"Error": "Invalid Session Ticket usage.", "code": 403, "Result": "false"}), 403
    if Platform != "Quest":
        return jsonify({"Error": "Invalid Platform.", "code": 403, "Result": "false"}), 403

    return jsonify({"PlayFabId": PlayFabId, "SessionTicket": SessionTicket,
                    "Platform": Platform, "Result": "true"}), 200


@app.route("/api/ConsumeOculusIAP", methods=["POST"])
def consume_oculus_iap():
    rjson   = request.get_json() or {}
    nonce   = rjson.get("nonce")
    user_id = rjson.get("userID")
    sku     = rjson.get("sku")
    response = requests.post(
        url=(f"https://graph.oculus.com/consume_entitlement"
             f"?nonce={nonce}&user_id={user_id}&sku={sku}"
             f"&access_token={settings.AppCreds}"),
        headers={"Content-Type": "application/json"}, timeout=10
    )
    if response.json().get("success"):
        return jsonify({"result": True})
    return jsonify({"error": True})


@app.route("/api/photon", methods=["POST", "GET"])
def severalsAnyUpdatePhotonAuth():
    print(f"[Photon] {request.method} request")
    AuthTicketUrl = f"https://{settings.TitleId}.playfabapi.com/Server/AuthenticateSessionTicket"
    VALID_APPS    = [settings.TitleId]

    if request.method == "GET":
        # Same checks as POST (this used to accept anyone). Photon may send the values as query parameters.
        q = {k.lower(): v for k, v in request.args.items()}
        newData = {
            "AppId":      q.get("appid"),
            "AppVersion": q.get("appversion"),
            "Ticket":     q.get("ticket") or q.get("token"),
            "Token":      q.get("token"),
            "Nonce":      q.get("nonce"),
            "Platform":   q.get("platform"),
        }
    else:
        newData = request.get_json(force=True, silent=True) or {}

    AppId      = newData.get("AppId")
    AppVersion = newData.get("AppVersion")
    Ticket     = newData.get("Ticket")
    Token      = newData.get("Token")
    Nonce      = newData.get("Nonce")
    Platform   = newData.get("Platform")

    if not Ticket:
        return jsonify({"ResultCode": 3, "Message": "Failed to parse token",
                        "Error": "BadRequest-NoTicket"}), 400
    if AppId not in VALID_APPS:
        return jsonify({"ResultCode": 2, "Message": "Invalid AppId",
                        "Error": "BadRequest-WrongAppId"}), 403
    if Platform != "Quest":
        return jsonify({"ResultCode": 3, "Message": "Platform Must Be Quest",
                        "Error": "BadRequest-BadPlatform"}), 403

    AuthReq = requests.post(url=AuthTicketUrl, json={"SessionTicket": Ticket},
                            headers=settings.ServerAuthHeaders(), timeout=10)
    if AuthReq.status_code != 200:
        return jsonify({"ResultCode": 2, "Message": "Invalid SessionTicket",
                        "Error": "BadRequest-BadSessionTicket"}), 403

    getdata  = AuthReq.json().get("data", {}).get("UserInfo", {})
    UserId   = getdata.get("PlayFabId")
    CustomId = getdata.get("CustomIdInfo", {}).get("CustomId", "")

    if "OCULUS" not in CustomId:
        return jsonify({"ResultCode": 3, "Message": "Invalid CustomId format",
                        "Error": "BadRequest-BadCustomId"}), 403

    OrgScopedCustomId = CustomId.split("OCULUS")[1]
    GetOculusIdReq    = requests.get(
        url=f"https://graph.oculus.com/{OrgScopedCustomId}?access_token={settings.AppCreds}",
        headers={"Content-Type": "application/json"}, timeout=10
    )
    if "error" in GetOculusIdReq.json():
        return jsonify({"ResultCode": 3, "Message": "Failed OrgScope check",
                        "Error": "BadRequest-InvalidOrgScopeId"}), 403

    if not UserId or len(UserId) != 16:
        return jsonify({"ResultCode": 3, "Message": "Bad UserId",
                        "Error": "BadRequest-BadUserId"}), 403

    OculusId       = GetOculusIdReq.json().get("id")
    VerifyNonceReq = requests.post(
        url="https://graph.oculus.com/user_nonce_validate",
        json={"access_token": settings.AppCreds, "nonce": Nonce, "user_id": str(OculusId)},
        headers={"Content-Type": "application/json"}, timeout=10
    )
    try:
        nonce_data = VerifyNonceReq.json()
    except Exception:
        nonce_data = {}
    print(nonce_data)

    # "is_valid" must be True (before, any reply that merely contained the word passed, even is_valid: false)
    if VerifyNonceReq.status_code != 200 or nonce_data.get("is_valid") is not True:
        return jsonify({"ResultCode": 1, "Message": "Failed Nonce Verification",
                        "Error": "BadRequest-InvalidNonce"}), 403

    return jsonify({
        "ResultCode": 1, "Message": "Yay Servers Work Ig",
        "AppId": AppId, "AppVersion": AppVersion, "Nonce": Nonce,
        "OculusId": OculusId, "Ticket": Ticket, "Token": Token, "UserId": UserId
    }), 200


@app.route("/", methods=["POST", "GET"])
def main():
    if request.method != "POST":
        return "", 404
    return "", 200

@app.route("/api/ReturnQueueStats", methods=["POST"])
def ReturnQueueStats():
    rjson = request.get_json() or {}
    return jsonify({"QueueName": rjson.get("queueName"), "PlayerCount": -1}), 200

@app.route("/api/CheckForBadName", methods=["POST"])
def CheckForBadName():
    return jsonify({"result": 0, "banLength": -1}), 200

@app.route("/api/GetAcceptedAgreements", methods=["POST"])
def GetAcceptedAgreements():
    rjson = request.get_json() or {}
    return jsonify({"TOS": rjson.get("TOS", "11.05.22.2"),
                    "PrivacyPolicy": rjson.get("PrivacyPolicy", "2024.03.07")}), 200

@app.route("/api/SubmitAcceptedAgreements", methods=["POST"])
def SubmitAcceptedAgreements():
    return "Agreements submitted successfully", 200

@app.route("/api/GetUserAge", methods=["POST"])
def GetUserAge():
    return jsonify(-1), 200

@app.route("/api/GetQuestStatus", methods=["POST"])
def get_quest_status_norm():
    daily  = {"quest1": random.randint(5, 20), "quest2": random.randint(5, 20)}
    weekly = {1: random.randint(10, 50), 2: random.randint(10, 50)}
    total  = random.randint(100, 500)
    wtotal = min(sum(daily.values()) + sum(weekly.values()), 100)
    return jsonify({"result": {"dailyPoints": daily, "weeklyPoints": weekly,
                               "userPointsTotal": total, "weeklyPointsTotal": wtotal}})

@app.route("/api/SetQuestComplete", methods=["POST", "GET"])
def setwestcompleter():
    daily  = {"quest1": random.randint(5, 20), "quest2": random.randint(5, 20)}
    weekly = {1: random.randint(10, 50), 2: random.randint(10, 50)}
    total  = random.randint(100, 500)
    wtotal = min(sum(daily.values()) + sum(weekly.values()), 100)
    return jsonify({"result": {"dailyPoints": daily, "weeklyPoints": weekly,
                               "userPointsTotal": total, "weeklyPointsTotal": wtotal}})

@app.route('/api/TitleData', methods=['POST', 'GET'])
def titledata():
    return jsonify({
        "AutoMuteCheckedHours": {"hours": 169},
        "AutoName_Adverbs": ["Cool","Fine","Bald","Bold","Half","Only","Calm","Fab","Ice","Mad","Rad","Big","New","Old","Shy"],
        "AutoName_Nouns": ["Gorilla","Chicken","Darling","Sloth","King","Queen","Royal","Major","Actor","Agent","Elder","Honey","Nurse","Doctor","Rebel","Shape","Ally","Driver","Deputy"],
        "CreditsData": [
            {"Title": "<color=#00FFFF>FOUNDERS</color>",
             "Entries": ["UNBORN", "GLACIAL"]},
            {"Title": "<color=yellow>SECOND FOUNDER</color>", "Entries": ["FATE"]},
            {"Title": "<color=white>AXIS TAG</color>", "Entries": ["discord.gg/BZhzeWz2nP"]}
        ],
        "BundleBoardSign":      "<color=#00FFFF>discord.gg/BZhzeWz2nP</color>",
        "BundleKioskButton":    "<color=#00FFFF>discord.gg/BZhzeWz2nP</color>",
        "BundleKioskSign":      "<color=#00FFFF>discord.gg/BZhzeWz2nP</color>",
        "BundleLargeSign":      "<color=#00FFFF>discord.gg/BZhzeWz2nP</color>",
        "EmptyFlashbackText":   "AXIS TAG\n\ndiscord.gg/BZhzeWz2nP",
        "EnableCustomAuthentication": True,
        "GorillanalyticsChance": 4320,
        "LatestPrivacyPolicyVersion": "2024.09.20",
        "LatestTOSVersion":     "2024.09.20",
        "MOTD": ("<color=#00FFFF>WELCOME TO AXIS TAG</color>\n"
                 "<color=#FFFF00>JOIN THE DISCORD:</color> <color=#00FFFF>discord.gg/BZhzeWz2nP</color>\n"
                 "<color=#FFFFFF>IF YOU FIND ANY ISSUES PLEASE REPORT THEM IN THE DISCORD SERVER. THANK YOU.</color>"),
        "SeasonalStoreBoardSign": "<color=#00FFFF>discord.gg/BZhzeWz2nP</color>",
        "TOS_2024.09.20":         "discord.gg/BZhzeWz2nP",
        "TOBAlreadyOwnCompTxt":   "discord.gg/BZhzeWz2nP",
        "TOBAlreadyOwnPurchaseBundle": "ALREADY OWNED",
        "TOBDefCompTxt":          "AXIS TAG",
        "TOBDefPurchaseBtnDefTxt": "AXIS TAG",
        "UseLegacyIAP": False
    })


@app.route("/api/RequestFriend", methods=["POST"])
def add_fwen():
    fwen          = request.get_json() or {}
    id            = fwen.get("PlayFabId")
    their_link_id = fwen.get("FriendFriendLinkId")
    if id and their_link_id:
        friend_requests.setdefault(id, set()).add(their_link_id)
        friend_requests.setdefault(their_link_id, set()).add(id)
    return jsonify({"success": True, "message": "Friend request sent.",
                    "PlayFabId": id, "FriendFriendLinkId": their_link_id})


@app.route("/api/GetFriendsV2", methods=["POST"])
def get_fwens_v2():
    fwen = request.get_json() or {}
    id   = fwen.get("PlayFabId")
    if not id or id not in friend_requests:
        return jsonify({"result": {"Friends": [], "myPrivacyState": 0},
                        "PlayFabId": id, "PlayFabTicket": fwen.get("PlayFabTicket")}), 200
    friends_list = []
    for friend_id in friend_requests[id]:
        username      = friend_usernames.get(friend_id) or get_username_from_playfab(friend_id)
        presence_info = friend_presence.get(friend_id, {
            "Zone": fwen.get("Zone"), "RoomId": fwen.get("RoomId"),
            "Region": fwen.get("Region"), "IsPublic": fwen.get("IsPublic")
        })
        friends_list.append({
            "Presence": {"FriendLinkId": friend_id, "UserName": username, **presence_info},
            "Created": "2025-03-21T08:46:01.713"
        })
    return jsonify({"result": {"Friends": friends_list, "myPrivacyState": 1},
                    "PlayFabId": id, "PlayFabTicket": fwen.get("PlayFabTicket")}), 200


@app.route("/api/RemoveFriend", methods=["POST"])
def remove_fren():
    r             = request.get_json() or {}
    pf_id         = r.get("PlayFabId")
    their_fren_id = r.get("FriendFriendLinkId")
    if pf_id in friend_requests:
        friend_requests[pf_id].discard(their_fren_id)
    if their_fren_id in friend_requests:
        friend_requests[their_fren_id].discard(pf_id)
    return jsonify({"success": True, "message": "Friend removed.",
                    "PlayFabId": pf_id, "FriendFriendLinkId": their_fren_id})


@app.route("/api/SetPrivacyState", methods=["POST"])
def set_privacy_state():
    return jsonify({"StatusCode": 200, "Error": None})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
