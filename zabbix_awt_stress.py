import argparse
import json
import subprocess
import time
from typing import List

import requests


API_ENDPOINT = "/api_jsonrpc.php"


def api_call(url: str, method: str, params: dict, auth: str | None = None) -> dict:
    """Generic helper for calling the Zabbix API."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    if auth:
        payload["auth"] = auth
    response = requests.post(
        f"{url}{API_ENDPOINT}",
        headers={"Content-Type": "application/json-rpc"},
        data=json.dumps(payload),
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    if "error" in result:
        raise RuntimeError(result["error"])
    return result["result"]


def login(url: str, user: str, password: str) -> str:
    return api_call(url, "user.login", {"user": user, "password": password})


def get_single_id(url: str, auth: str, method: str, name: str) -> str:
    """Retrieve a single object ID by name using Zabbix API."""
    result = api_call(
        url,
        method,
        {"filter": {"name": name}},
        auth,
    )
    if not result:
        raise RuntimeError(f"{method} returned no results for {name}")
    return result[0]["groupid" if method == "hostgroup.get" else "templateid"]


def create_hosts(url: str, auth: str, count: int, group_id: str, template_id: str) -> List[str]:
    host_ids = []
    for i in range(count):
        host_name = f"awt_host_{i+1}"
        params = {
            "host": host_name,
            "interfaces": [
                {
                    "type": 1,
                    "main": 1,
                    "useip": 1,
                    "ip": "127.0.0.1",
                    "dns": "",
                    "port": "10050",
                }
            ],
            "groups": [{"groupid": group_id}],
            "templates": [{"templateid": template_id}],
        }
        result = api_call(url, "host.create", params, auth)
        host_ids.append(result["hostids"][0])
    return host_ids


def stress_test(server: str, hosts: List[str], nvps: int, duration: int) -> None:
    """Send metrics using zabbix_sender to reach desired NVPS."""
    end = time.time() + duration
    index = 0
    while time.time() < end:
        start = time.time()
        for _ in range(nvps):
            host = hosts[index % len(hosts)]
            index += 1
            cmd = [
                "zabbix_sender",
                "-z",
                server,
                "-s",
                host,
                "-k",
                "test.item",
                "-o",
                str(time.time()),
            ]
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        if elapsed < 1:
            time.sleep(1 - elapsed)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create hosts and run stress test")
    parser.add_argument("url", help="Zabbix server URL, e.g., http://localhost")
    parser.add_argument("user", help="Zabbix username")
    parser.add_argument("password", help="Zabbix password")
    parser.add_argument("host_count", type=int, help="Number of hosts to create")
    parser.add_argument("nvps", type=int, help="Target new values per second")
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duration of stress test in seconds (default: 60)",
    )
    parser.add_argument(
        "--server",
        default="127.0.0.1",
        help="Hostname or IP address of Zabbix server for zabbix_sender",
    )
    args = parser.parse_args()

    auth = login(args.url, args.user, args.password)
    group_id = get_single_id(args.url, auth, "hostgroup.get", "AWT 6.0")
    template_id = get_single_id(args.url, auth, "template.get", "linux_new_awt")
    hosts = create_hosts(args.url, auth, args.host_count, group_id, template_id)
    stress_test(args.server, [f"awt_host_{i+1}" for i in range(args.host_count)], args.nvps, args.duration)


if __name__ == "__main__":
    main()
