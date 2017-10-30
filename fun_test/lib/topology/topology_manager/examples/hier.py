from ..topo_manager import *

def main():
            
    topo = Topology()
    topo.create(2,2,4)
    import pdb; pdb.set_trace()
    topo.create(5,8,32)
    topo.save()
    topo.printRacks([1])
    topo.pauseRacks([2, 15, 9, 6])
    topo.unpauseRacks([2, 15, 9, 6])
    topo.pauseNodes(['1-2', '0-1', '0-3', '5-8', '6-3', '10-1', '8-10'])
    topo.unpauseNodes(['1-2', '0-1', '0-3', '5-8', '6-3', '10-1', '8-10'])
    topo.linkImpair('1-1', 'all spine links')
    topo.linkRepair('1-1', 'all spine links')
    topo.linkImpair('5-1', 'all inter-f1 links')
    topo.linkRepair('5-1', 'all inter-f1 links')
    topo.linkImpair('10-1', 'all inter-f1 links')
    topo.linkRepair('9-10', 'all inter-f1 links')
    topo.linkImpair('1-1', ['1-3', '0-2', '0-3', '5-1', '6-3', '10-1', '8-10'])
    topo.linkRepair('1-1', ['1-3', '0-2', '0-3', '5-1', '6-3', '10-1', '8-10'])

    tg1 = topo.attachTG('1-1')
    tg2 = topo.attachTG('3-2')
    tg3 = topo.attachTG('5-4')
    tgx = topo.attachTG('3-10')
    tgx = topo.attachTG('6-1')
  
    topo.save()

    out = tg1.start_iperf(tg2)
    print out
    out = tg1.start_ab(tg3)
    print out

    ''' 
    topo = Topology()
    topo.load()
    pretty(json.loads(topo.getAccessInfo()))
    import pdb; pdb.set_trace()
    # Fetching TGs after doing a topo.load()
    tg1=topo.get_tgs('1-1')[0]
    tg2=topo.get_tg('TG1-3-2')
    tg3=topo.get_tg('TG1-5-4')

    out = tg1.start_iperf(tg2)
    print out
    out = tg1.start_ab(tg3)
    print out

    tgx = topo.attachTG('8-1')
    tg2 = topo.attachTG('4-4')
    tg3 = topo.attachTG('3-4')

    out = tg1.start_iperf(tg2)
    print out
    out = tg2.start_ab(tg3)
    print out

    topo.linkImpair('1-1', 'all spine links', 'loss', '10%', '25%')
    topo.linkRepair('1-1', 'all spine links')
    topo.linkImpair('2-1', 'all spine links', 'delay', '50ms', '10ms', 'normal')
    topo.linkRepair('2-1', 'all spine links')
    topo.linkImpair('9-1', 'all spine links', 'rate', '1mbit', '32kbit', '40ms')
    topo.linkRepair('9-1', 'all spine links')
    topo.linkImpair('10-1', 'all spine links', 'duplicate', '10%')
    topo.linkRepair('3-10', 'all spine links')
    topo.linkImpair('1-1', 'all spine links', 'corrupt', '10%')
    topo.linkRepair('1-1', 'all spine links')
    topo.linkImpair('1-1', 'all spine links', 'reorder', '10%', '50%', '10ms')
    topo.linkRepair('1-1', 'all spine links')

    topo.cleanup()
    ''' 

if __name__ == "__main__":
    main()
