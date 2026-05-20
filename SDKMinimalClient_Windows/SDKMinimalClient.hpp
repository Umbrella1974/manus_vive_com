#ifndef _SDK_MINIMAL_CLIENT_HPP_
#define _SDK_MINIMAL_CLIENT_HPP_


// Set up a Doxygen group.
/** @addtogroup SDKMinimalClient
 *  @{
 */


#include "ClientPlatformSpecific.hpp"
#include "ManusSDK.h"
#include <cstdint>
#include <mutex>
#include <vector>
#include <string>

// Windows Socket headers
#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#define SOCKET_TYPE SOCKET
#define INVALID_SOCKET_VAL INVALID_SOCKET
#define CLOSE_SOCKET closesocket
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#define SOCKET_TYPE int
#define INVALID_SOCKET_VAL -1
#define CLOSE_SOCKET close
#endif

 /// @brief The type of connection to core.
enum class ConnectionType : int
{
	ConnectionType_Invalid = 0,
	ConnectionType_Integrated,
	ConnectionType_Local,
	ConnectionType_Remote,
	ClientState_MAX_CLIENT_STATE_SIZE
};

/// @brief Values that can be returned by this application.
enum class ClientReturnCode : int
{
	ClientReturnCode_Success = 0,
	ClientReturnCode_FailedPlatformSpecificInitialization,
	ClientReturnCode_FailedToResizeWindow,
	ClientReturnCode_FailedToInitialize,
	ClientReturnCode_FailedToFindHosts,
	ClientReturnCode_FailedToConnect,
	ClientReturnCode_UnrecognizedStateEncountered,
	ClientReturnCode_FailedToShutDownSDK,
	ClientReturnCode_FailedPlatformSpecificShutdown,
	ClientReturnCode_FailedToRestart,
	ClientReturnCode_FailedWrongTimeToGetData,

	ClientReturnCode_MAX_CLIENT_RETURN_CODE_SIZE
};

/// @brief Used to store the information about the skeleton data coming from the estimation system in Core.
class ClientRawSkeleton
{
public:
	RawSkeletonInfo info;
	std::vector<SkeletonNode> nodes;
};

/// @brief Used to store all the skeleton data coming from the estimation system in Core.
class ClientRawSkeletonCollection
{
public:
	std::vector<ClientRawSkeleton> skeletons;
	uint64_t publishTime = 0;
	uint64_t receiveMonotonicMs = 0;
	uint64_t callbackIndex = 0;
};

/// @brief Used to store all the tracker data coming from Core.
class TrackerDataCollection
{
public:
	std::vector<TrackerData> trackerData;
	uint64_t publishTime = 0;
	uint64_t receiveMonotonicMs = 0;
	uint64_t callbackIndex = 0;
};

class SDKMinimalClient : public SDKClientPlatformSpecific
{
public:
	SDKMinimalClient();
	~SDKMinimalClient();
	ClientReturnCode Initialize();
	ClientReturnCode InitializeSDK();
	ClientReturnCode ShutDown();
	ClientReturnCode RegisterAllCallbacks();
	void Run();

	void PrintRawSkeletonNodeInfo();

	static void OnRawSkeletonStreamCallback(const SkeletonStreamInfo* const p_RawSkeletonStreamInfo);
	static void OnTrackerStreamCallback(const TrackerStreamInfo* const p_TrackerStreamInfo);

	// Add: Socket related functions
	bool InitializeSocket();
	void CloseSocket();
	void SendSkeletonData(const ClientRawSkeletonCollection* data);
	void SendTrackerData(const TrackerDataCollection* data);
	std::string SkeletonToJSON(const ClientRawSkeletonCollection* data);
	std::string TrackerToJSON(const TrackerDataCollection* data);
	std::string CombinedToJSON(const ClientRawSkeletonCollection* skeletonData, const TrackerDataCollection* trackerData);
	bool SendJsonLine(const std::string& jsonData);

protected:

	ClientReturnCode Connect();

	static SDKMinimalClient* s_Instance;
	bool m_Running = true;
	bool m_PrintedNodeInfo = false;

	ConnectionType m_ConnectionType = ConnectionType::ConnectionType_Invalid;

	std::mutex m_RawSkeletonMutex;
	ClientRawSkeletonCollection* m_NextRawSkeleton = nullptr;
	ClientRawSkeletonCollection* m_RawSkeleton = nullptr;
	uint64_t m_SkeletonCallbackCounter = 0;

	// Add: Tracker related member variables
	std::mutex m_TrackerMutex;
	TrackerDataCollection* m_NextTrackerData = nullptr;
	TrackerDataCollection* m_TrackerData = nullptr;
	uint64_t m_TrackerCallbackCounter = 0;

	uint32_t m_FrameCounter = 0;

	// Add: Socket related member variables
	SOCKET_TYPE m_ClientSocket = INVALID_SOCKET_VAL;
	bool m_SocketInitialized = false;
	std::string m_PythonHost = "127.0.0.1";
	int m_PythonPort = 8888;
};

// Close the Doxygen group.
/** @} */
#endif
