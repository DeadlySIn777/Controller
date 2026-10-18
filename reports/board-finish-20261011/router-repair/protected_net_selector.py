"""Read-only routing eligibility; never loads pcbnew, edits copper, or starts a router.

Unknown nets require review. Eligibility only permits an additive ordinary-signal
pass; it does not authorize deleting existing copper or prove a route's quality.
Source scopes follow docs/MOTHERBOARD_IS2.md retained interface/fault contracts.
Exact plane, pair, power and zone-net sets must come from the board/run inputs.
"""
import re


CRITICAL_SCOPES = {
    "fpga_core", "mc_motor_buffers", "mc_permission", "mc_local_power",
    "watchdog_conditioning", "motherboard_motors", "motherboard_motor_power",
    "motherboard_power_entry", "motherboard_safety_sensor", "motherboard_operator",
    "motherboard_fast_inputs", "motherboard_process", "motherboard_analog_input",
    "motherboard_analog_output", "motherboard_compute", "motherboard_comms",
    "motherboard_io_control", "motherboard_acc_control", "motherboard_di",
    "motherboard_do", "motherboard_esp_socket",
}
MOTION = re.compile(r"(?:^|[/_])(?:STEP\d*|DIR\d*|ENC\d+|MPG)(?:[/_]|$)")
FAULT = re.compile(r"(?:ALM|ALARM|FAULT|PERMIT|HEALTH|SAFE|SAFETY|STO|WATCHDOG|WDT|WD_|RESET|ARM|ENABLE|(?:^|[/_])EN\d)")
TIMING = re.compile(r"(?:CLK|CLOCK|OSC|SCLK|SPI|MISO|MOSI|USB|TMDS|HDMI|DSI|CSI|RGMII|PCIE|I2C|SDA|SCL|UART|CAN|RS485)")
POWER = re.compile(r"(?:GND|(?:^|[/_])COM(?:[/_]|$)|VREF|PGOOD|PWR|RAIL|FEED|(?:^|_)\d+(?:V\d*)?(?:V|V\d+)(?:_|$))")
INDICATOR = re.compile(
    r"^/motherboard_status/(?:RGB_DRIVER_\d+|OBS\d+_[AK]|"
    r"OUT\d+_[RGB]_(?:MID|K)|RGB_(?:MOTION|OUTPUT|NETWORK)_[RGB]_(?:K|MID))$"
)


def normalize(name):
    if not isinstance(name, str) or not name:
        raise ValueError("net identity must be a nonempty string")
    return name.replace("{slash}", "/")


class Selector:
    def __init__(self, plane_nets=(), pair_nets=(), power_nets=(), zone_nets=()):
        self.exact = {
            "plane_pour_return": {normalize(n) for n in plane_nets},
            "high_speed_pair": {normalize(n) for n in pair_nets},
            "power_table": {normalize(n) for n in power_nets},
            "owns_copper_zone": {normalize(n) for n in zone_nets},
        }

    def select(self, name):
        net = normalize(name)
        reasons = [category for category, names in self.exact.items() if net in names]
        parts = net.split("/")
        if len(parts) > 2 and parts[1] in CRITICAL_SCOPES:
            reasons.append("retained_critical_source_scope")
        for category, expression in (("motion_encoder", MOTION), ("fault_permission", FAULT),
                                     ("timing_communication", TIMING), ("power_reference", POWER)):
            if expression.search(net.upper() if category != "motion_encoder" else net):
                reasons.append(category)
        if reasons:
            return {"net": net, "disposition": "protected", "reasons": reasons, "eligible": False}
        if INDICATOR.fullmatch(net):
            return {"net": net, "disposition": "ordinary_indicator", "reasons": ["explicit_indicator_family"], "eligible": True}
        return {"net": net, "disposition": "review_required", "reasons": ["unclassified_source_net"], "eligible": False}


def select_jobs(jobs, selector):
    """Partition a saved job list without hiding excluded jobs or mutating input."""
    eligible, withheld = [], []
    for index, job in enumerate(jobs, 1):
        if not isinstance(job, dict) or not isinstance(job.get("net"), str):
            raise ValueError(f"job {index} lacks a source net identity")
        decision = selector.select(job["net"])
        record = {"source_job_index": index, "decision": decision, "job": job}
        (eligible if decision["eligible"] else withheld).append(record)
    return eligible, withheld
