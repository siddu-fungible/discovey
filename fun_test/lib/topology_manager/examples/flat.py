from ..topolib import *

def main():
                        
    topo = Topology()
    topo.create(1,50,0)
    topo.save()
    topo.printRacks([1])
    topo.pauseRacks([2])
    topo.unpauseRacks([2])
    topo.pauseNodes(['1-2', '0-1', '0-3', '0-15', '0-25', '0-35', '0-49', '0-51', '0-200'])
    topo.unpauseNodes(['1-2', '0-1', '0-3', '0-15', '0-25', '0-35', '0-49', '0-51', '0-200'])
    topo.linkImpair('0-1', 'all spine links')
    topo.linkRepair('0-1', 'all spine links')
    topo.linkImpair('0-1', ['1-3', '0-2', '0-3', '0-21', '0-39', '0-49', '0-51', '0-200'])
    topo.linkRepair('0-1', ['1-3', '0-2', '0-3', '0-21', '0-39', '0-49', '0-51', '0-200'])
    topo.linkImpair('0-45', ['1-3', '0-2', '0-3', '0-21'])
    topo.linkRepair('0-45', ['1-3', '0-2', '0-3', '0-21'])

    tg1 = topo.attachTG('0-1')
    tg2 = topo.attachTG('0-35')
    tg3 = topo.attachTG('0-49')
    tgx = topo.attachTG('0-51')
    tgx = topo.attachTG('0-200')

    out = tg1.start_iperf(tg2)
    print out
    out = tg1.start_ab(tg3)
    print out

    pretty(json.loads(topo.getAccessInfo()))

    topo.save()

    '''
    topo = Topology()
    topo.load()
    tg4 = topo.attachTG('0-3')
    tg5 = topo.attachTG('0-29')
    tg6 = topo.attachTG('0-44')

    topo.save()

    # Fetching existing TGs
    tg1=topo.get_tgs('0-1')[0]
    tg2=topo.get_tg('TG1-0-35')
    tg3=topo.get_tg('TG1-0-49')

    out = tg1.start_iperf(tg2)
    print out
    out = tg1.start_ab(tg3)
    print out
    out = tg1.start_iperf(tg4)
    print out
    out = tg5.start_ab(tg6)
    print out

    topo.printRacks([1])
    topo.pauseRacks([2])
    topo.unpauseRacks([2])
    topo.pauseNodes(['1-2', '0-1', '0-3', '0-15', '0-25', '0-35', '0-49', '0-51'])
    topo.unpauseNodes(['1-2', '0-1', '0-3', '0-15', '0-25', '0-35', '0-49', '0-51'])
    topo.linkImpair('0-1', 'all spine links')
    topo.linkRepair('0-1', 'all spine links')
    topo.linkImpair('0-1', ['1-3', '0-2', '0-3', '0-21', '0-39', '0-49'])
    topo.linkRepair('0-1', ['1-3', '0-2', '0-3', '0-21', '0-39', '0-49'])
    topo.linkImpair('0-45', ['1-3', '0-2', '0-3', '0-21'])
    topo.linkRepair('0-45', ['1-3', '0-2', '0-3', '0-21'])

    topo.cleanup()
    '''         

if __name__ == "__main__":
    main()
