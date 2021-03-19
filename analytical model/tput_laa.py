import sys
import sympy as sym
sym.init_printing()

# UNITS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
us = 10**-6
ms = 10**-3
Mbps = 10**6
B = 8
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#%% CONSTANTS %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-----------------------------------------
sigma = 9 * us
#-----------------------------------------
SIFS = 16 * us
DIFS = 34 * us
AIFSN = 2
#-------------
basic_rate_wifi = 6 * Mbps
#-------------
ACK_framesize_wifi = 14 * B
BACK_framesize_wifi = 32 * B
T_phy_wifi = 40 * us
MPDU_delimiter = 4 * B
MAC_headersize_wifi = 34 * B
LLC_header_wifi = 8 * B
ACK_timeout_wifi = 50 * us

#-----------------------------------------
laa_slot_duration = 0.5 * ms
laa_average_delay_access_to_tx_start = laa_slot_duration/2
#-----------------------------------------
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


def compute_tao_equations():
    ## CWr = min(CWmin*2**r, CWmax)
    b00,PC,PB,r,z,tao_wifi,tao_laa,CWmin,CWmax,M_CWmax,M,n_w,n_l,aifsn,ml,CCA_min,pfc,m_l = sym.symbols("b00,PC,PB,r,z,tao_wifi,tao_laa,CWmin,CWmax,M_CWmax,M,n_w,n_l,aifsn,ml,CCA_min,pfc,m_l")
    b00_expr = 1 / ( sym.Sum(((PC**r)*(1 + (2+(1-PB)*(CWmin*2**r-1))/(2*(1-PB)))), (r,0,M_CWmax)) + sym.Sum(((PC**r)*(1 + (2+(1-PB)*(CWmax-1))/(2*(1-PB)))), (r,M_CWmax+1,M)) )

    tao_expr = b00 * sym.Sum(PC**r,(r,0,M))

    PC_laa_expr = 1 - ((1-tao_laa)**(n_l-1))
    PB_laa_expr = 1 - ((1-tao_laa)**(n_l-1))

    tao_expr = tao_expr.subs(b00, b00_expr)
    tao_laa_expr = tao_expr.subs(PC, PC_laa_expr)
    tao_laa_expr = tao_laa_expr.subs(PB, PB_laa_expr)

    return tao_laa_expr


def compute_tao_values(tao_laa_expr, CWmin_laa, CWmax_laa, M_CWmax_laa, M_laa, m_laa, n_laa):
    b00,PC,PB,r,z,tao_wifi,tao_laa,CWmin,CWmax,M_CWmax,M,n_w,n_l,aifsn,ml,CCA_min,pfc,m_l = sym.symbols("b00,PC,PB,r,z,tao_wifi,tao_laa,CWmin,CWmax,M_CWmax,M,n_w,n_l,aifsn,ml,CCA_min,pfc,m_l")

    tao_laa_expr = tao_laa_expr.subs(m_l,m_laa)
    tao_laa_expr = tao_laa_expr.subs(CWmin, CWmin_laa)
    tao_laa_expr = tao_laa_expr.subs(CWmax, CWmax_laa)
    tao_laa_expr = tao_laa_expr.subs(M_CWmax, M_CWmax_laa)
    tao_laa_expr = tao_laa_expr.subs(M, M_laa)
    tao_laa_expr = tao_laa_expr.subs(m_l, m_laa)
    tao_laa_expr = tao_laa_expr.subs(n_l, n_laa)
    tao_laa_expr = tao_laa_expr.simplify()

    tao_laa_eq = sym.Eq(tao_laa,tao_laa_expr)
    res = sym.nsolve(tao_laa_eq,tao_laa, 0, prec=100, verify=False)
    return res


def compute_throughput(tao_laa, n_laa, txop_laa,data_rate_laa):
    P_idle = ((1-tao_laa)**n_laa)
    P_succ_tx_laa = n_laa * tao_laa * ((1-tao_laa)**(n_laa-1))
    P_coll_ll = 1 - ((1-tao_laa)**(n_laa)) - (n_laa * tao_laa * ((1-tao_laa)**(n_laa-1)))

    T_laa_succ_tx = T_laa_coll = txop_laa+laa_average_delay_access_to_tx_start
    T_contention_slot = (P_succ_tx_laa*T_laa_succ_tx) + (P_coll_ll*T_laa_coll) + (P_idle*sigma)

    throughput_laa = (13/14) * (data_rate_laa/T_contention_slot) * (P_succ_tx_laa*txop_laa)

    return throughput_laa/Mbps



##########################################################################################################

def get_wifi_datarate(bw):
    if bw == 20:
        return 86.7 * Mbps
    elif bw == 40:
        return 200 * Mbps
    elif bw == 80:
        return 433.3 * Mbps
    elif bw == 160:
        return 866.7 * Mbps
    else:
        return 0

def get_wifi_max_txop(bw,ampdu_exponent,payload_size):
    if bw == 20:
        return 5.484 * ms
    elif bw == 40 or bw == 80 or bw == 160:
        MAX_aggregated_MDPUs = 64
        MAC_max_length = min((2**(13+ampdu_exponent) -1) * B, MAX_aggregated_MDPUs * (MPDU_delimiter+MAC_headersize_wifi+LLC_header_wifi+payload_size))
        return min(5.484 * ms, T_phy_wifi + (MAC_max_length / get_wifi_datarate(bw)))
    else:
        return 0

def get_laa_datarate(bw):
    if bw == 20:
        return 75.4 * Mbps
    elif bw == 40:
        return 150.8 * Mbps
    elif bw == 60:
        return 226.1 * Mbps
    elif bw == 80:
        return 301.5 * Mbps
    elif bw == 100:
        return 376.9 * Mbps
    elif bw == 120:
        return 2 * get_laa_datarate(60)
    elif bw == 140:
        return get_laa_datarate(80) + get_laa_datarate(60)
    elif bw == 160:
        return 2 * get_laa_datarate(80)
    else:
        return 0

def get_laa_channel_access_params(laa_class,coexistence=True):
    if laa_class == 1:
        txop_laa = 2 * ms
        CWmin_laa = 4
        CWmax_laa = 16
        M_CWmax_laa = 2
        M_laa = 6
        m_laa = 1
        return txop_laa, CWmin_laa, CWmax_laa, M_CWmax_laa, M_laa, m_laa
    elif laa_class == 4:
        txop_laa = 8 * ms if coexistence else 10 * ms
        CWmin_laa = 16
        CWmax_laa = 1024
        M_CWmax_laa = 6
        M_laa = 10
        m_laa = 7
        return txop_laa, CWmin_laa, CWmax_laa, M_CWmax_laa, M_laa, m_laa
    else:
        raise Exception("Invalid LAA class ({})".format(laa_class))
        sys.exit()


##########################################################################################################


def main():
    tx_window = None

    if len(sys.argv) >= 4:
        n_laa = int(sys.argv[1])
        bw = int(sys.argv[2])
        laa_class = int(sys.argv[3])
        if len(sys.argv) == 5:
            tx_window = float(sys.argv[4]) * ms
    else:
        print("No input arguments provided!!!")
        sys.exit()

    tao_laa_expr = compute_tao_equations()
    data_rate_laa = get_laa_datarate(bw)
    max_txop_laa, CWmin_laa, CWmax_laa, M_CWmax_laa, M_laa, m_laa = get_laa_channel_access_params(laa_class,coexistence=False)
    average_access_to_medium = laa_average_delay_access_to_tx_start

    tao_laa = compute_tao_values(tao_laa_expr, CWmin_laa, CWmax_laa, M_CWmax_laa, M_laa, m_laa, n_laa)

    if tx_window is None or tx_window < (max_txop_laa + average_access_to_medium):
        num_bursts_with_max_txop_laa = 1
        remainder_burst_duration = 0
        txop_laa = tx_window - average_access_to_medium if tx_window is not None else max_txop_laa
    else:
        num_bursts_with_max_txop_laa = int(tx_window/(max_txop_laa + average_access_to_medium)) if max_txop_laa > 0 else 0
        remainder_burst_duration = tx_window % (max_txop_laa + average_access_to_medium) if max_txop_laa > 0 else 0
        txop_laa = max_txop_laa

    if remainder_burst_duration == 0:
        tput_laa = compute_throughput(tao_laa, n_laa, txop_laa,data_rate_laa)
    else:
        tput_laa_long_bursts = compute_throughput(tao_laa, n_laa, txop_laa,data_rate_laa)
        tput_laa_remainder_burst = compute_throughput(tao_laa, n_laa, remainder_burst_duration,data_rate_laa)
        tput_laa = ( (tx_window-remainder_burst_duration) * tput_laa_long_bursts + remainder_burst_duration * tput_laa_remainder_burst ) / tx_window
    print(f"n_laa: {n_laa}\tBW: {bw}\tLAA class: {laa_class}\tTX window: {tx_window}\tThroughput LAA: {float(tput_laa):.5f}")

if __name__ == "__main__":
    main()
