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
T_phy_wifi = 40 * us # 21.3.2 VHT PPDU format de https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=7786995  | 20 * us en 11n
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

    PC_wifi_expr = 1 - ((1-tao_laa)**n_l) * ((1-tao_wifi)**(n_w-1))
    PC_laa_expr = 1 - ((1-pfc)+pfc*((1-tao_wifi)**n_w)) * ((1-tao_laa)**(n_l-1))
    PB_wifi_expr = 1 - ( ((1-tao_laa)**n_l) * ((1-tao_wifi)**(n_w-1)) ) ** (aifsn-CCA_min+1)
    PB_laa_expr = 1 - ( ((1-tao_wifi)**n_w) * ((1-tao_laa)**(n_l-1)) ) ** ((m_l+1)-CCA_min+1)

    tao_expr = tao_expr.subs(b00, b00_expr)
    tao_wifi_expr = tao_expr.subs(PC, PC_wifi_expr)
    tao_wifi_expr = tao_wifi_expr.subs(PB, PB_wifi_expr)
    tao_laa_expr = tao_expr.subs(PC, PC_laa_expr)
    tao_laa_expr = tao_laa_expr.subs(PB, PB_laa_expr)

    return tao_wifi_expr, tao_laa_expr


def compute_tao_values(tao_wifi_expr, tao_laa_expr, CWmin_wifi, CWmax_wifi, M_CWmax_wifi, M_wifi, CWmin_laa, CWmax_laa, M_CWmax_laa, M_laa, m_laa, n_wifi, n_laa,txop_wifi):
    b00,PC,PB,r,z,tao_wifi,tao_laa,CWmin,CWmax,M_CWmax,M,n_w,n_l,aifsn,ml,CCA_min,pfc,m_l = sym.symbols("b00,PC,PB,r,z,tao_wifi,tao_laa,CWmin,CWmax,M_CWmax,M,n_w,n_l,aifsn,ml,CCA_min,pfc,m_l")

    CCA_min_expr = min(AIFSN,m_laa+1)
    tao_wifi_expr = tao_wifi_expr.subs(CCA_min,CCA_min_expr)
    tao_wifi_expr = tao_wifi_expr.subs(aifsn,AIFSN)
    tao_wifi_expr = tao_wifi_expr.subs(m_l,m_laa)
    Pfc = min(1,txop_wifi/laa_slot_duration)
    tao_wifi_expr = tao_wifi_expr.subs(pfc,Pfc)
    tao_wifi_expr = tao_wifi_expr.subs(CWmin, CWmin_wifi)
    tao_wifi_expr = tao_wifi_expr.subs(CWmax, CWmax_wifi)
    tao_wifi_expr = tao_wifi_expr.subs(M_CWmax, M_CWmax_wifi)
    tao_wifi_expr = tao_wifi_expr.subs(M, M_wifi)
    tao_wifi_expr = tao_wifi_expr.subs(m_l, m_laa)
    tao_wifi_expr = tao_wifi_expr.subs(n_w, n_wifi)
    tao_wifi_expr = tao_wifi_expr.subs(n_l, n_laa)
    tao_wifi_expr = tao_wifi_expr.simplify()

    tao_laa_expr = tao_laa_expr.subs(CCA_min,CCA_min_expr)
    tao_laa_expr = tao_laa_expr.subs(aifsn,AIFSN)
    tao_laa_expr = tao_laa_expr.subs(m_l,m_laa)
    tao_laa_expr = tao_laa_expr.subs(pfc,Pfc)
    tao_laa_expr = tao_laa_expr.subs(CWmin, CWmin_laa)
    tao_laa_expr = tao_laa_expr.subs(CWmax, CWmax_laa)
    tao_laa_expr = tao_laa_expr.subs(M_CWmax, M_CWmax_laa)
    tao_laa_expr = tao_laa_expr.subs(M, M_laa)
    tao_laa_expr = tao_laa_expr.subs(m_l, m_laa)
    tao_laa_expr = tao_laa_expr.subs(n_w, n_wifi)
    tao_laa_expr = tao_laa_expr.subs(n_l, n_laa)
    tao_laa_expr = tao_laa_expr.simplify()

    tao_wifi_eq = sym.Eq(tao_wifi,tao_wifi_expr)
    tao_laa_eq = sym.Eq(tao_laa,tao_laa_expr)
    res = sym.nsolve([tao_wifi_eq,tao_laa_eq],(tao_wifi,tao_laa), [0,0], prec=100, verify=False, solver='bisect')
    return res


def compute_throughput(tao_wifi, tao_laa, n_wifi, n_laa, payload_size,txop_wifi,data_rate_wifi, txop_laa,data_rate_laa):
    Pfc = min(1,txop_wifi/laa_slot_duration)
    P_idle = ((1-tao_wifi)**n_wifi) * ((1-tao_laa)**n_laa)

    P_succ_tx_wifi = n_wifi * tao_wifi * ((1-tao_wifi)**(n_wifi-1)) * ((1-tao_laa)**n_laa)
    P_succ_tx_laa = n_laa * tao_laa * ((1-tao_laa)**(n_laa-1)) * ((1-tao_wifi)**n_wifi)

    P_coll_ww = ((1-tao_laa)**n_laa) * (1 - ((1-tao_wifi)**n_wifi) - (n_wifi * tao_wifi * ((1-tao_wifi)**(n_wifi-1))) ) if n_wifi > 1 else 0
    P_coll_ll = ((1-tao_wifi)**n_wifi) * (1 - ((1-tao_laa)**n_laa) - (n_laa * tao_laa * ((1-tao_laa)**(n_laa-1))) ) if n_laa > 1 else 0
    P_coll_wl = (1 - ((1-tao_wifi)**n_wifi)) * (1 - ((1-tao_laa)**n_laa)) if n_wifi > 0 and n_laa > 0 else 0

    num_mpdus_per_ampdu = int((txop_wifi-T_phy_wifi)/((MPDU_delimiter+MAC_headersize_wifi+LLC_header_wifi+payload_size)/data_rate_wifi))

    T_wifi_succ_tx = (SIFS + sigma*AIFSN) + T_phy_wifi + num_mpdus_per_ampdu * ((MPDU_delimiter+MAC_headersize_wifi+LLC_header_wifi+payload_size)/data_rate_wifi) + SIFS + BACK_framesize_wifi/basic_rate_wifi
    T_wifi_coll = (SIFS + sigma*AIFSN) + T_phy_wifi + num_mpdus_per_ampdu * ((MPDU_delimiter+MAC_headersize_wifi+LLC_header_wifi+payload_size)/data_rate_wifi) + ACK_timeout_wifi
    T_laa_succ_tx = T_laa_coll = txop_laa+laa_average_delay_access_to_tx_start
    T_contention_slot = (P_succ_tx_wifi*T_wifi_succ_tx) + (P_succ_tx_laa*T_laa_succ_tx) + (P_coll_ww*T_wifi_coll) + (P_coll_ll*T_laa_coll) + (P_coll_wl*max(T_wifi_coll,T_laa_coll)) + (P_idle*sigma)

    throughput_wifi = (P_succ_tx_wifi * num_mpdus_per_ampdu * payload_size) / T_contention_slot
    throughput_laa = (13/14) * (data_rate_laa/T_contention_slot) * (P_succ_tx_laa*txop_laa + P_coll_wl*(int(max(0,T_laa_coll-T_wifi_coll)/laa_slot_duration)*laa_slot_duration))

    return throughput_wifi/Mbps, throughput_laa/Mbps


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
    payload_size = 1500 * B
    CWmin_wifi = 16
    CWmax_wifi = 1024
    M_CWmax_wifi = 6
    M_wifi = 7

    if len(sys.argv) == 7:
        n_wifi = int(sys.argv[1])
        n_laa = int(sys.argv[2])
        bw = int(sys.argv[3])
        ampdu_exponent = int(sys.argv[4])
        payload_size = int(sys.argv[5]) * B
        laa_class = int(sys.argv[6])
    else:
        print("No input arguments provided!!!")
        sys.exit()

    tao_wifi_expr, tao_laa_expr = compute_tao_equations()
    txop_wifi = get_wifi_max_txop(bw,ampdu_exponent,payload_size)
    data_rate_wifi = get_wifi_datarate(bw)
    data_rate_laa = get_laa_datarate(bw)

    txop_laa, CWmin_laa, CWmax_laa, M_CWmax_laa, M_laa, m_laa = get_laa_channel_access_params(laa_class,coexistence=True)
    tao_wifi, tao_laa = compute_tao_values(tao_wifi_expr, tao_laa_expr, CWmin_wifi, CWmax_wifi, M_CWmax_wifi, M_wifi, CWmin_laa, CWmax_laa, M_CWmax_laa, M_laa, m_laa, n_wifi, n_laa, txop_wifi)
    tput_wifi, tput_laa = compute_throughput(tao_wifi, tao_laa, n_wifi, n_laa, payload_size,txop_wifi,data_rate_wifi, txop_laa,data_rate_laa)
    print(f"n_wifi: {n_wifi}\tn_laa: {n_laa}\tBW: {bw}\tA-MPDU exponent: {ampdu_exponent}\tPayload size: {payload_size/B} B\tLAA class: {laa_class}\tThroughput Wi-Fi: {float(tput_wifi):.5f}\tThroughput LAA: {float(tput_laa):.5f}\tThroughput Aggregated: {float(tput_wifi+tput_laa):.5f}")


if __name__ == "__main__":
    main()
