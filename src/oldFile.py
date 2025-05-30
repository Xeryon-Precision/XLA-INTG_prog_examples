import sys

import canopen
from config import *
from helpers import *

DOWNLOAD_TRACEBUFFER = False


# TODO: PDO mode will not yet work
USE_PDO = False

# logging.basicConfig(level=logging.DEBUG)

network, absolute_path = setup_network(eds_path)
network.check()

# Add node based on EDS file
node = canopen.BaseNode402(32, absolute_path)
network.add_node(node)

# Reset node
node.nmt.state = 'RESET'
node.nmt.wait_for_bootup(15)

#node.nmt.state = 'RESET COMMUNICATION'

node.sdo.RESPONSE_TIMEOUT = 10.0

print(f'Node Status {node.nmt.state}:{node.state}')

# # Iterate over arrays or records
# error_log = node.sdo[0x1003]
# for error in error_log.values():
#     print(f"Error {error.raw} was found in the log")

for node_id in network:
    print(network[node_id])

# Transmit SYNC every 100 ms
#network.sync.start(0.1)

node.tpdo.read()
node.rpdo.read()

node.load_configuration()

print(f'Node Status {node.nmt.state}:{node.state}')

node.setup_402_state_machine()

print(f'Node Status {node.nmt.state}:{node.state}')

#device_name = node.sdo[0x1008].raw
vendor_id = node.sdo[0x1018][1].raw

#print(device_name)
print("%08X" % vendor_id)

# Check active TPDO mappings in the library
for tpdo_index, tpdo in node.tpdo.items():
    print(f"TPDO {tpdo_index}: COB-ID = {tpdo.cob_id:#04x}, Transmission Type = {tpdo.trans_type}, enabled = {tpdo.enabled}, is_periodic = {tpdo.is_periodic}")
    for var in tpdo.map:
        print(f"  Mapped object: {var.name} (Index: {var.index:#04x}, Subindex: {var.subindex})")

for rpdo_index, rpdo in node.rpdo.items():
    print(f"RPDO {rpdo_index}: COB-ID = {rpdo.cob_id:#04x}, Transmission Type = {rpdo.trans_type}, enabled = {rpdo.enabled}, is_periodic = {rpdo.is_periodic}")
    for var in rpdo.map:
        print(f"  Mapped object: {var.name} (Index: {var.index:#04x}, Subindex: {var.subindex})")

# state machine only works if NMT is in OPERATIONAL mode
node.nmt.state = 'OPERATIONAL'
print(f'Node Status {node.nmt.state}:{node.state}')

switch_state(node, 'SWITCH ON DISABLED')
switch_state(node, 'READY TO SWITCH ON')
switch_state(node, 'SWITCHED ON')

if USE_PDO:
    node.rpdo[3].start(0.1)

# -----------------------------------------------------------------------------------------

print('Node booted up')
print(' FW ID %s' % (node.sdo[0x5004].raw) )

# -----------------------------------------------------------------------------------------
# create a list of positions to walk through
positions = list(range(-4000, 4000, 1000))
positions.extend(list(range(4000, -4000, -1000)))
step_delay = 0.5
# -----------------------------------------------------------------------------------------
#node.nmt.start_node_guarding(0.01)
nloops = 0
while True:
    # node.sdo[0x5000].raw = 3 + 8
    node.sdo[0x5000].raw = 0

    # switch to homing mode
    set_control_mode(node, "MODE_HOMING")

    # enable operation
    switch_state(node, 'OPERATION ENABLED')

    # set home offset
    # node.sdo[0x607C].raw = 0

    # trigger homing
    do_homing(node, P402_HOMING_METHOD_NEG_INDEX)
    # do_homing(node, P402_HOMING_METHOD_POS_INDEX)

    try:
        switch_state(node, 'READY TO SWITCH ON')
        switch_state(node, 'SWITCHED ON')

        # switch to position profile mode
        set_control_mode(node, "MODE_TRAJECTORY")

        # set home offset
        # node.sdo[0x607C].raw = 0

        # set postion window
        node.sdo[0x6067].raw = 5 # position window
        node.sdo[0x6068].raw = 50 # position window time

        switch_state(node, 'OPERATION ENABLED')

        for target_pos in positions:
            try:
                network.check()
            except Exception:
                break

            print(f"Set pos to {target_pos}")

            # enable trace buffer on new target
            node.sdo[0x5003][5].raw=1

            # set the new target point
            if USE_PDO:
                # TODO: this probably won't work due to timing
                # e.g. when is this sent and how can we do the trigger
                #      on the control word?
                node.rpdo[3]['Target Position'].raw = target_pos
            else:
                node.sdo[0x607A].raw = target_pos

            # trigger the update

            # set new set-point bit
            curr_val = node.sdo[0x6040].raw # needed because node.controlword is read-only
            node.controlword = curr_val | 0x0010

            # wait for ack
            print("waiting for ack")
            wait_for_statusword_flags(node, 0x1000, expected_flag_state=True)

            # clear the set-point bit for next iteration
            curr_val = node.sdo[0x6040].raw # needed because node.controlword is read-only
            node.controlword = curr_val & ~0x0010

            # wait for arrival
            print("waiting for arrival")
            wait_for_statusword_flags(node, 0x0400, expected_flag_state=True)

            current_pos = node.sdo[0x6064].raw
            print(f" -> read-back pos is {current_pos}\n")

            if DOWNLOAD_TRACEBUFFER:
                nloops += 1
                read_tracebuffer(node, outfile="outfile-%d.txt" % nloops, length=1024)

            ## Read a value from TxPDO1
            #node.tpdo[1].wait_for_reception()
            #speed = node.tpdo[1]['Velocity actual value'].phys

            # Read the state of the Statusword
            statusword = node.sdo[0x6041].raw

            print(f'statusword: {statusword}')
            #print(f'VEL: {speed}')
            print(f'Node Status {node.nmt.state}:{node.state}')

            time.sleep(step_delay)
    except:
        print("failed comms")
        time.sleep(5)
