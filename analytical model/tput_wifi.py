import sys
import sympy as sym
sym.init_printing()

# Unidades %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
us = 10**-6
ms = 10**-3
Mbps = 10**6
B = 8
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#%% CONSTANTES %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#-----------------------------------------
sigma = 9 * us# duracion de un slot
#-----------------------------------------
SIFS = 16 * us
DIFS = 34 * us
AIFSN = 2
#-------------
basic_rate_wifi = 6 * Mbps# DR, 80 MHz
#-------------
ACK_framesize_wifi = 14 * B
BACK_framesize_wifi = 32 * B
T_phy_wifi = 40 * us # 20 * us en 11n
MPDU_delimiter = 4 * B
MAC_headersize_wifi = 34 * B
LLC_header_wifi = 8 * B
#print("Cambios hechos: en 11n, la cabecera phy es de 20us. En 11ac con A-MPDU (https://www.oreilly.com/library/view/80211ac-a-survival/9781449357702/ch03.html) la cabecera son 40 us de phy y luego concatenaciones de delimiter+MAC+payload.")
#print("Cambio con respecto al paper de las formulas: Adaptado a A-MPDU, tenemos DIFS,PHY, y N*(delimiter+MAC+LLC+payload). Se añade LLC. Se cambia ACK por block ACK")
#print("Cambio con respecto al paper de las formulas: Adaptado a A-MPDU, colisiona en la primera MPDU. Se añade LLC")
# Quitar los 'if data_rate_wifi > 0 else 0' que meti para automatizar todos los anchos de banda posibles, incluyendo los de LAA que Wi-Fi no soporta
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

    PC_wifi_expr = 1 - ((1-tao_wifi)**(n_w-1))
    PB_wifi_expr = 1 - ((1-tao_wifi)**(n_w-1))

    tao_expr = tao_expr.subs(b00, b00_expr)
    tao_wifi_expr = tao_expr.subs(PC, PC_wifi_expr)
    tao_wifi_expr = tao_wifi_expr.subs(PB, PB_wifi_expr)

    return tao_wifi_expr


def compute_tao_values(tao_wifi_expr, CWmin_wifi, CWmax_wifi, M_CWmax_wifi, M_wifi, n_wifi):
    b00,PC,PB,r,z,tao_wifi,tao_laa,CWmin,CWmax,M_CWmax,M,n_w,n_l,aifsn,ml,CCA_min,pfc,m_l = sym.symbols("b00,PC,PB,r,z,tao_wifi,tao_laa,CWmin,CWmax,M_CWmax,M,n_w,n_l,aifsn,ml,CCA_min,pfc,m_l")

    CCA_min_expr = AIFSN
    tao_wifi_expr = tao_wifi_expr.subs(CCA_min,CCA_min_expr)
    tao_wifi_expr = tao_wifi_expr.subs(aifsn,AIFSN)
    tao_wifi_expr = tao_wifi_expr.subs(CWmin, CWmin_wifi)
    tao_wifi_expr = tao_wifi_expr.subs(CWmax, CWmax_wifi)
    tao_wifi_expr = tao_wifi_expr.subs(M_CWmax, M_CWmax_wifi)
    tao_wifi_expr = tao_wifi_expr.subs(M, M_wifi)
    tao_wifi_expr = tao_wifi_expr.subs(n_w, n_wifi)
    tao_wifi_expr = tao_wifi_expr.simplify()

    tao_wifi_eq = sym.Eq(tao_wifi,tao_wifi_expr)
    res = sym.nsolve(tao_wifi_eq,tao_wifi, 0, prec=100, verify=False)
    return res


def compute_throughput(tao_wifi, n_wifi, payload_size,txop_wifi,data_rate_wifi):
    P_idle = ((1-tao_wifi)**n_wifi)
    P_succ_tx_wifi = n_wifi * tao_wifi * ((1-tao_wifi)**(n_wifi-1))

    P_coll_ww = ( 1 - ((1-tao_wifi)**(n_wifi)) - (n_wifi * tao_wifi * ((1-tao_wifi)**(n_wifi-1))) )
    num_mpdus_per_ampdu = int((txop_wifi-T_phy_wifi)/((MPDU_delimiter+MAC_headersize_wifi+LLC_header_wifi+payload_size)/data_rate_wifi)) if data_rate_wifi > 0 else 0

    T_wifi_succ_tx = (SIFS + sigma*AIFSN) + T_phy_wifi + num_mpdus_per_ampdu * ((MPDU_delimiter+MAC_headersize_wifi+LLC_header_wifi+payload_size)/data_rate_wifi) + SIFS + BACK_framesize_wifi/basic_rate_wifi if data_rate_wifi > 0 else 0
    T_wifi_coll = (SIFS + sigma*AIFSN) + T_phy_wifi + num_mpdus_per_ampdu * ((MPDU_delimiter+MAC_headersize_wifi+LLC_header_wifi+payload_size)/data_rate_wifi) + ACK_timeout_wifi if data_rate_wifi > 0 else 0
    T_contention_slot = (P_succ_tx_wifi*T_wifi_succ_tx) + (P_coll_ww*T_wifi_coll) + (P_idle*sigma)

    throughput_wifi = (P_succ_tx_wifi * num_mpdus_per_ampdu * payload_size) / T_contention_slot

    return throughput_wifi/Mbps


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
    CWmin_wifi = 16
    CWmax_wifi = 1024
    M_CWmax_wifi = 6
    M_wifi = 7
    tx_window = None

    if len(sys.argv) >= 5:
        n_wifi = int(sys.argv[1])
        bw = int(sys.argv[2])
        ampdu_exponent = int(sys.argv[3])
        payload_size = int(sys.argv[4]) * B
        if len(sys.argv) == 6:
            tx_window = float(sys.argv[5]) * ms
    else:
        print("No input arguments provided!!!")
        sys.exit()

    tao_wifi_expr = compute_tao_equations()
    max_txop_wifi = get_wifi_max_txop(bw,ampdu_exponent,payload_size)
    data_rate_wifi = get_wifi_datarate(bw)
    average_access_to_medium = SIFS + (AIFSN*sigma) + (sigma*CWmin_wifi/2)

    tao_wifi = compute_tao_values(tao_wifi_expr, CWmin_wifi, CWmax_wifi, M_CWmax_wifi, M_wifi, n_wifi)

    if tx_window is None or tx_window < (max_txop_wifi + average_access_to_medium):
        num_bursts_with_max_txop_wifi = 1
        remainder_burst_duration = 0
        txop_wifi = tx_window - average_access_to_medium if tx_window is not None else max_txop_wifi
    else:
        num_bursts_with_max_txop_wifi = int(tx_window/(max_txop_wifi + average_access_to_medium)) if max_txop_wifi > 0 else 0
        remainder_burst_duration = tx_window % (max_txop_wifi + average_access_to_medium) if max_txop_wifi > 0 else 0
        txop_wifi = max_txop_wifi

    if remainder_burst_duration == 0:
        tput_wifi = compute_throughput(tao_wifi, n_wifi, payload_size, txop_wifi, data_rate_wifi)
    else:
        tput_wifi_long_bursts = compute_throughput(tao_wifi, n_wifi, payload_size,txop_wifi,data_rate_wifi)
        tput_wifi_remainder_burst = compute_throughput(tao_wifi, n_wifi, payload_size,remainder_burst_duration,data_rate_wifi)
        tput_wifi = ( (tx_window-remainder_burst_duration) * tput_wifi_long_bursts + remainder_burst_duration * tput_wifi_remainder_burst ) / tx_window
    print(f"n_wifi: {n_wifi}\tBW: {bw}\tA-MPDU exponent: {ampdu_exponent}\tPayload size: {payload_size/B} B\tTX window: {tx_window}\tThroughput Wi-Fi: {float(tput_wifi):.5f}")


if __name__ == "__main__":
    main()
