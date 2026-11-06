// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title Model provenance for federated, learning-driven Zero-Trust access control (claim C3).
/// @notice The FL coordinator commits every round's global model hash plus the hashes of the client
/// updates behind it. Gateways commit digests of their access decisions, each tagged with the model
/// version that made them. A round found poisoned later can be revoked, which tells every gateway
/// to roll back and lists (via events) which decisions to audit. Enforcement never waits for the
/// chain: gateways decide locally and these writes are asynchronous.
contract Provenance {
    struct Round {
        bytes32 model;        // sha256 of the aggregated global model
        bytes32 clientsRoot;  // sha256 over the client update hashes, in order
        uint32 nClients;
        uint64 committedAt;
        bool revoked;
    }

    address public immutable coordinator;
    mapping(address => bool) public gateways;
    mapping(uint256 => Round) public rounds;
    mapping(bytes32 => uint256) public roundOfModel;  // model hash -> round (0 = unknown)
    uint256 public latestRound;

    event RoundCommitted(uint256 indexed round, bytes32 indexed model, bytes32 clientsRoot, bytes32[] clientUpdates,
                         uint32[] clientSizes, uint32 valF1e6);
    event DecisionsCommitted(address indexed gateway, bytes32 indexed model, uint64 tFrom, uint64 tTo, uint32 n,
                             bytes32 digest);
    event RoundRevoked(uint256 indexed round, bytes32 indexed model, string reason);

    error NotCoordinator();
    error NotGateway();
    error UnknownModel(bytes32 model);
    error RoundOrder(uint256 expected, uint256 got);

    constructor() {
        coordinator = msg.sender;
    }

    modifier onlyCoordinator() {
        if (msg.sender != coordinator) revert NotCoordinator();
        _;
    }

    function setGateway(address gw, bool allowed) external onlyCoordinator {
        gateways[gw] = allowed;
    }

    function commitRound(uint256 round, bytes32 model, bytes32[] calldata clientUpdates, uint32[] calldata clientSizes,
                         uint32 valF1e6) external onlyCoordinator {
        if (round != latestRound + 1) revert RoundOrder(latestRound + 1, round);
        bytes32 root = sha256(abi.encodePacked(clientUpdates));
        rounds[round] = Round(model, root, uint32(clientUpdates.length), uint64(block.timestamp), false);
        roundOfModel[model] = round;
        latestRound = round;
        emit RoundCommitted(round, model, root, clientUpdates, clientSizes, valF1e6);
    }

    function commitDecisions(bytes32 model, uint64 tFrom, uint64 tTo, uint32 n, bytes32 digest) external {
        if (!gateways[msg.sender]) revert NotGateway();
        if (roundOfModel[model] == 0) revert UnknownModel(model);  // decisions must cite a committed model
        emit DecisionsCommitted(msg.sender, model, tFrom, tTo, n, digest);
    }

    function revokeRound(uint256 round, string calldata reason) external onlyCoordinator {
        rounds[round].revoked = true;
        emit RoundRevoked(round, rounds[round].model, reason);
    }

    /// @notice Gateways call this before loading a model: false for unknown or revoked models.
    function isTrusted(bytes32 model) external view returns (bool) {
        uint256 r = roundOfModel[model];
        return r != 0 && !rounds[r].revoked;
    }
}
