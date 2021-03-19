#include "ns3/command-line.h"
#include "ns3/config.h"
#include "ns3/uinteger.h"
#include "ns3/boolean.h"
#include "ns3/double.h"
#include "ns3/string.h"
#include "ns3/log.h"
#include "ns3/yans-wifi-helper.h"
#include "ns3/ssid.h"
#include "ns3/mobility-helper.h"
#include "ns3/internet-stack-helper.h"
#include "ns3/ipv4-address-helper.h"
#include "ns3/udp-client-server-helper.h"
#include "ns3/packet-sink-helper.h"
#include "ns3/on-off-helper.h"
#include "ns3/ipv4-global-routing-helper.h"
#include "ns3/packet-sink.h"
#include "ns3/yans-wifi-channel.h"

#include "ns3/point-to-point-module.h"
#include "ns3/udp-socket-factory.h"
#include "ns3/mac-low.h"
#include "ns3/wifi-net-device.h"
#include "ns3/wifi-mac.h"
#include "ns3/regular-wifi-mac.h"
#include "ns3/net-device-queue-interface.h"
#include "ns3/queue-limits.h"
#include "ns3/queue.h"
#include "ns3/wifi-mac-queue.h"
#include "ns3/ocb-wifi-mac.h"
#include "ns3/v4ping-helper.h"

using namespace ns3;
NS_LOG_COMPONENT_DEFINE("test-uvigo");

void StartNotificationApp(Ptr<Socket> socket, Time wifiTransmissionDuration, Time laaTransmissionDuration);
void NotifyWifiAps(Ptr<Socket> socket, Time notificationTimestamp, Time wifiTransmissionDuration, Time laaTransmissionDuration);
void NotificationReceivedByWifiAp (Ptr<Socket> socket);
void NotifyOrchestrator (Ptr<Socket> socket);
void NotificationReceivedByOrchstrator (Ptr<Socket> socket);
void ReserveMedium(Ptr<ns3::MacLow> mac_low, Time duration, bool pauseTransmissions);

struct NotificationWifiStructure {
  Time notificationTimestamp;
  Time wifiTransmissionDuration;
  Time laaTransmissionDuration;
};
Time ctsTransmissionDuration = MicroSeconds(36);
Time sifs = MicroSeconds(16);
Time ackTransmissionDuration = MicroSeconds(36)+sifs;


void StartNotificationApp(Ptr<Socket> notification_app_socket, Time wifiTransmissionDuration, Time laaTransmissionDuration) {
    NotifyWifiAps(notification_app_socket, ns3::Simulator::Now(), wifiTransmissionDuration, laaTransmissionDuration);
    Simulator::Schedule(wifiTransmissionDuration+laaTransmissionDuration+ctsTransmissionDuration, &StartNotificationApp, notification_app_socket, wifiTransmissionDuration, laaTransmissionDuration);
}

void NotifyWifiAps(Ptr<Socket> socket, Time notificationTimestamp, Time wifiTransmissionDuration, Time laaTransmissionDuration) {
    struct NotificationWifiStructure packetStruct = {notificationTimestamp, wifiTransmissionDuration, laaTransmissionDuration};
    Ptr<Packet> packet = Create<Packet> ((uint8_t*)&packetStruct, sizeof(NotificationWifiStructure));
    socket->Send (packet);
}
void NotificationReceivedByWifiAp (Ptr<Socket> socket) {
    Ptr<Packet> packet = socket->Recv();
    struct NotificationWifiStructure packetStruct;
    packet->CopyData((uint8_t*)&packetStruct, packet->GetSize());
    Time notificationTimestamp = packetStruct.notificationTimestamp;
    Time wifiTransmissionDuration = packetStruct.wifiTransmissionDuration;
    Time laaTransmissionDuration = packetStruct.laaTransmissionDuration;

    Ptr<ns3::MacLow> mac_low = socket->GetNode()->GetDevice(0)->GetObject<WifiNetDevice>()->GetMac()->GetObject<RegularWifiMac>()->m_low;
    mac_low->setEndOfTransmissionWindow(notificationTimestamp + wifiTransmissionDuration - ackTransmissionDuration);
    Simulator::Schedule((notificationTimestamp-ns3::Simulator::Now())+wifiTransmissionDuration, &ReserveMedium, mac_low, laaTransmissionDuration, true);

    NotifyOrchestrator(socket);
}

void NotifyOrchestrator (Ptr<Socket> socket) {
    int m_packetSize = 8;
    Ptr<Packet> packet = Create<Packet>(m_packetSize);
    socket->Send (packet);
}
void NotificationReceivedByOrchstrator (Ptr<Socket> socket) {
    Ptr<Packet> packet = socket->Recv ();
}

void ReserveMedium(Ptr<ns3::MacLow> mac_low, Time duration, bool pauseTransmissions) {
    mac_low->ReserveMedium(duration,true);
}
// End of Orchestrator



int main(int argc, char *argv[]) {
    // Simulation parameters
    bool udp = true;
    bool useRts = false;
    double distance = 1.0;  // meters
    int mcs = 9;  // -1 indicates an unset value
    int channelWidth = 20;
    int sgi = 1;
    double pingStartTime = 0.5;  // seconds
    double pingStopTime = 1;  // seconds
    double txStartTimeSeconds = 1;  // seconds
    double simulationTime = 10;  // seconds
    double wifiTransmissionDurationVal = 10; // ms
    double laaTransmissionDurationVal = 10; // ms
    bool doNotMultiplex = false;
    int ampduExponent = 7;

    CommandLine cmd(__FILE__);
    cmd.AddValue("distance", "Distance in meters between the station and the access point", distance);
    cmd.AddValue("simulationTime", "Simulation time in seconds", simulationTime);
    cmd.AddValue("udp", "UDP if set to 1, TCP otherwise", udp);
    cmd.AddValue("useRts", "Enable/disable RTS/CTS", useRts);
    cmd.AddValue("mcs", "if set, limit testing to a specific MCS (0-9)", mcs);
    cmd.AddValue("channelWidth", "Channel width, in MHz", channelWidth);
    cmd.AddValue("sgi", "Short guard interval {0,1}", sgi);
    cmd.AddValue("wifiOnTime", "Wi-Fi ON time (ms)", wifiTransmissionDurationVal);
    cmd.AddValue("laaOnTime", "LTE LAA ON time (ms)", laaTransmissionDurationVal);
    cmd.AddValue("doNotMultiplex", "Regular throughput simulation", doNotMultiplex);
    cmd.AddValue("ampduExponent", "Maximum A-MPDU length exponent", ampduExponent);
    cmd.Parse(argc, argv);

    // Checks
    if (mcs < 0 || mcs > 9) {
        NS_LOG_ERROR("[src/wifi/examples/test-uvigo.cc] mcs takes a non expected value!");
        exit(1);
    }
    if (channelWidth != 20 && channelWidth != 40 && channelWidth != 80 && channelWidth != 160) {
        NS_LOG_ERROR("[src/wifi/examples/test-uvigo.cc] channelWidth takes a non expected value!");
        exit(1);
    }
    if (mcs == 9 && channelWidth == 20) {
        NS_LOG_INFO("[src/wifi/examples/test-uvigo.cc] Changing MCS to 8, as 9 is not supported for 20 MHz");
        mcs = 8;
    }
    if (ampduExponent < 0 || ampduExponent > 7) {
        NS_LOG_ERROR("[src/wifi/examples/test-uvigo.cc] ampduExponent takes a non expected value!");
        exit(1);
    }

    if (useRts) {
        Config::SetDefault("ns3::WifiRemoteStationManager::RtsCtsThreshold", StringValue("0"));
    }
    uint32_t payloadSize;  // 1500 byte IP packet
    if (udp) {
        payloadSize = 1472;  // bytes
    } else { //Tcp
        payloadSize = 1448;  // bytes
        Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(payloadSize));
    }


// Set up ------------------------------------------------------------------------------------------------------------------------------------
    // Wi-Fi devices set up
    NodeContainer wifiApNode;
    wifiApNode.Create(1);
    NodeContainer wifiStaNode;
    wifiStaNode.Create(1);
    // PHY
    YansWifiChannelHelper channel = YansWifiChannelHelper::Default();
    YansWifiPhyHelper phy = YansWifiPhyHelper::Default();
    phy.SetChannel(channel.Create());
    // Wi-Fi helper
    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211ac);
    std::ostringstream oss;
    oss << "VhtMcs" << mcs;
    wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager", "DataMode", StringValue(oss.str()), "ControlMode", StringValue(oss.str()));
    // MAC
    //  STA
    WifiMacHelper mac;
    Ssid ssid = Ssid("gti-uvigo");
    mac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssid));
    NetDeviceContainer staDevice;
    staDevice = wifi.Install(phy, mac, wifiStaNode);
    //  AP
    mac.SetType("ns3::ApWifiMac", "EnableBeaconJitter", BooleanValue(false), "Ssid", SsidValue(ssid));
    NetDeviceContainer apDevice;
    apDevice = wifi.Install(phy, mac, wifiApNode);
    // Set A-MPDU size
    int ampdusize = pow(2.0, 13+ampduExponent) - 1;
    Config::Set ("/NodeList/*/DeviceList/*/$ns3::WifiNetDevice/Mac/BE_MaxAmpduSize", UintegerValue (ampdusize));
    // Set channel width (all devices)
    Config::Set("/NodeList/*/DeviceList/*/$ns3::WifiNetDevice/Phy/ChannelWidth", UintegerValue(channelWidth));
    // Set guard interval
    Config::Set("/NodeList/*/DeviceList/*/$ns3::WifiNetDevice/HtConfiguration/ShortGuardIntervalSupported", BooleanValue(sgi));
    // Infinite queue
    Config::Set ("/NodeList/*/DeviceList/*/$ns3::WifiNetDevice/Mac/$ns3::RegularWifiMac/*/Queue/MaxSize", StringValue ("10000000p"));

    // Mobility
    MobilityHelper mobility;
    Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator>();
    positionAlloc->Add(Vector(0.0, 0.0, 0.0));
    positionAlloc->Add(Vector(distance, 0.0, 0.0));
    mobility.SetPositionAllocator(positionAlloc);
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
    mobility.Install(wifiApNode);
    mobility.Install(wifiStaNode);

    // Internet stack
    InternetStackHelper stack;
    stack.Install(wifiApNode);
    stack.Install(wifiStaNode);
    Ipv4AddressHelper address;
    address.SetBase("192.168.0.0", "255.255.255.0");
    Ipv4InterfaceContainer apNodeInterface;
    apNodeInterface = address.Assign(apDevice);
    Ipv4InterfaceContainer staNodeInterface;
    staNodeInterface = address.Assign(staDevice);

    // Ping app to populate ARP table before transmissions
    ApplicationContainer pingApps;
    Ipv4Address clientIPAddress = staNodeInterface.GetAddress(0, 0);
    V4PingHelper ping(clientIPAddress);
    pingApps.Add(ping.Install(wifiApNode.Get(0)));
    pingApps.Start(Seconds(pingStartTime));
    pingApps.Stop(Seconds(pingStopTime));

    // Data traffic application set up
    ApplicationContainer serverApp;
    if (udp) {
        // UDP flow
        uint16_t port = 9;
        UdpServerHelper server(port);
        serverApp = server.Install(wifiStaNode.Get(0));
        serverApp.Start(Seconds(0.0));
        serverApp.Stop(Seconds(simulationTime + txStartTimeSeconds));
        UdpClientHelper client(staNodeInterface.GetAddress(0), port);
        client.SetAttribute("MaxPackets", UintegerValue(4294967295u));
        client.SetAttribute("Interval", TimeValue(Time("0.00001")));  // packets/s
        client.SetAttribute("PacketSize", UintegerValue(payloadSize));
        ApplicationContainer clientApp = client.Install(wifiApNode.Get(0));
        clientApp.Start(Seconds(txStartTimeSeconds));
        clientApp.Stop(Seconds(simulationTime + txStartTimeSeconds));
    } else {
        // TCP flow
        uint16_t port = 50000;
        Address localAddress(InetSocketAddress(Ipv4Address::GetAny(), port));
        PacketSinkHelper packetSinkHelper("ns3::TcpSocketFactory", localAddress);
        serverApp = packetSinkHelper.Install(wifiStaNode.Get(0));
        serverApp.Start(Seconds(0.0));
        serverApp.Stop(Seconds(simulationTime + txStartTimeSeconds));
        OnOffHelper onoff("ns3::TcpSocketFactory", Ipv4Address::GetAny());
        onoff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
        onoff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
        onoff.SetAttribute("PacketSize", UintegerValue(payloadSize));
        onoff.SetAttribute("DataRate", DataRateValue(1000000000));  // bit/s
        AddressValue remoteAddress(InetSocketAddress(staNodeInterface.GetAddress(0), port));
        onoff.SetAttribute("Remote", remoteAddress);
        ApplicationContainer clientApp = onoff.Install(wifiApNode.Get(0));
        clientApp.Start(Seconds(txStartTimeSeconds));
        clientApp.Stop(Seconds(simulationTime + txStartTimeSeconds));
    }

    // Technology change notifier application (UDP)
    /// Network setup
    NodeContainer notifier_app_node;
    notifier_app_node.Create(1);
    InternetStackHelper technology_change_notifier_stack;
    technology_change_notifier_stack.Install(notifier_app_node);
    NodeContainer p2pNodes = NodeContainer(notifier_app_node, wifiApNode);
    PointToPointHelper pointToPoint;
    pointToPoint.SetDeviceAttribute("DataRate", StringValue("1000000Mbps"));
    pointToPoint.SetChannelAttribute("Delay", StringValue("0ms"));
    NetDeviceContainer notifier_devices = pointToPoint.Install(p2pNodes);
    Ipv4AddressHelper notifier_address;
    notifier_address.SetBase("10.0.0.0", "255.255.255.0");
    Ipv4InterfaceContainer notifier_interfaces = notifier_address.Assign(notifier_devices);
    Ipv4GlobalRoutingHelper::PopulateRoutingTables();
    // Application setup
    uint16_t notification_port = 1234;
    InetSocketAddress notification_wifi_ap_address(InetSocketAddress(notifier_interfaces.GetAddress(1), notification_port));
    InetSocketAddress notification_app_address(InetSocketAddress(notifier_interfaces.GetAddress(0), notification_port));
    Ptr<Socket> notification_wifi_ap_socket = Socket::CreateSocket(wifiApNode.Get(0), UdpSocketFactory::GetTypeId());
    notification_wifi_ap_socket->Bind(notification_wifi_ap_address);
    Ptr<Socket> notification_app_socket = Socket::CreateSocket(p2pNodes.Get(0), UdpSocketFactory::GetTypeId());
    notification_app_socket->Bind(notification_app_address);
    notification_wifi_ap_socket->Connect(notification_app_address);
    notification_app_socket->Connect(notification_wifi_ap_address);
    notification_wifi_ap_socket->SetRecvCallback(MakeCallback(&NotificationReceivedByWifiAp));
    notification_app_socket->SetRecvCallback(MakeCallback(&NotificationReceivedByOrchstrator));
    // scheduler
    if (!doNotMultiplex) {
        Simulator::Schedule(Seconds(txStartTimeSeconds), &StartNotificationApp, notification_app_socket, MicroSeconds(int(1000*wifiTransmissionDurationVal)), MicroSeconds(int(1000*laaTransmissionDurationVal)));
    }

    // Dump to PCAP
    phy.SetPcapDataLinkType(YansWifiPhyHelper::DLT_IEEE802_11_RADIO);
    phy.EnablePcap("dump", wifiStaNode);
    phy.EnablePcap("dump", wifiApNode);


    // Run simulation
    std::cout << "Results:\n\t- MCS value: " << mcs << "\n\t- Channel width: " << channelWidth << " MHz\n\t- Short guard interval: " << sgi << "\n\t----------------------" << std::endl;
    Simulator::Stop(Seconds(simulationTime + txStartTimeSeconds));
    Simulator::Run();

    // Collecting results
    uint64_t rxBytes = 0;
    if (udp) {
        rxBytes = payloadSize * DynamicCast<UdpServer>(serverApp.Get(0))->GetReceived();
    } else {
        rxBytes = DynamicCast<PacketSink>(serverApp.Get(0))->GetTotalRx();
    }
    double throughput = (rxBytes * 8) / (simulationTime * 1000000.0);  // Mbit/s
    Simulator::Destroy();

    // Print results
    std::cout << "\t- Throughput: " << throughput << " Mbit/s" << std::endl;

    return 0;
}
