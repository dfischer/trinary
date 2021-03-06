#!env python
# Created:20080516
# By Jeff Connelly
#
# Merge two PADS-PCB files

import sys, os

SHARED_SIGNALS = ("$G_Vdd", "$G_Vss", "0")

def load_pads(f):
    l = f.readline().strip()
    if l != "*PADS-PCB*":
        print "not PADS-PCB format, first line: %s" % (l,)
        raise SystemExit

    # Read comments until parts section
    while True:
        l = f.readline()
        if len(l) == 0:
            print "unexpected end-of-file before parts section"
            raise SystemExit
        if l.strip() == "*PART*":
            # got it
            break

    # Read all parts until *NET*
    parts = {}
    while True:
        part = f.readline()
        if len(part) == 0:
            print "Unexpected end-of-file while reading parts"
            raise SystemExit
            break

        part = part.strip()
        if len(part) == 0:  # (stripped)
            # whitespace
            continue 

        if part == "*NET*":
            break
        name, package = part.split()
        parts[name] = package

    # Read signals
    signal = None
    pins = []
    nets = {}
    while True:
        line = f.readline()
        if len(line) == 0:
            break

        line = line.strip()
        if line.startswith("*SIGNAL*"):
            if signal:
                nets[signal] = pins

            signal = line.split()[1]
            pins = []
        else:
            pins.extend(line.split())
    # Add last signal
    nets[signal] = pins

    return parts, nets

def save_pads(parts, net, name):
    out = "*PADS-PCB*\n"
    out += "*%s*\n" % (name,)
    out += "*PART*\n"
    for name, package in parts.iteritems():
        out += "%s %s\n" % (name, package)
    out += "*NET*\n"
    for signal in net:
        out += "*SIGNAL* %s\n" % (signal,)
        for pin in net[signal]:
            out += "%s\n" % (pin,)
    return out 

if len(sys.argv) != 3:
    print "usage: python mergepads.py file-1.pads file-2.pads"
    raise SystemExit

f1 = file(sys.argv[1], "rt")
f2 = file(sys.argv[2], "rt")

parts, nets = load_pads(f1)
parts2, nets2 = load_pads(f2)

# Merge part list
for name, package in parts2.iteritems():
    new_name = name
    if name in parts:
        # Need to rename part to avoid collision
        new_name += "_2"
        assert new_name not in parts, "Name %s in both netlists, even after suffixing" % (name,)

        # Go through pins and rename if needed
        for signal, pins in nets2.iteritems():
            new_pins = []
            for pin in pins:
                part_name, pin_no = pin.split(".")
                if part_name == name:
                    new_pins.append("%s.%s" % (new_name, pin_no))
                else:
                    new_pins.append("%s.%s" % (part_name, pin_no))
            nets2[signal] = new_pins

    parts[new_name] = package

# Merge nets
for signal in nets2:
    new_signal = signal
    if signal in nets and signal not in SHARED_SIGNALS:
        new_signal += "_2"
        # If this happens, improve suffixing (try alternatives)
        assert new_signal not in nets, "Signal %s in both netlists, even after suffix" % (new_signal,)

    if new_signal in SHARED_SIGNALS:
        nets[new_signal].extend(nets2[signal])
    else:
        nets[new_signal] = nets2[signal]

print save_pads(parts, nets, "%s + %s" % (sys.argv[1], sys.argv[2]))

