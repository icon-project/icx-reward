from typing import Dict, List, Optional

from iconsdk.exception import JSONRPCException

from icx_reward.types.constants import SYSTEM_ADDRESS
from icx_reward.types.exception import InvalidParamsException
from icx_reward.types.prep import Penalty
from icx_reward.rpc import RPC


class PenaltyEventSig:
    Imposed = "PenaltyImposed(Address,int,int)"
    Slash = "Slashed(Address,Address,int)"


class PenaltyFetcher:
    def __init__(self, rpc: RPC, address: str, start_height: int, end_height: int):
        self.__rpc = rpc
        self.__address = address
        self.__start_height = start_height
        self.__end_height = end_height
        self.__penalties: Dict[int, Penalty] = {}
        if not self.is_prep(self.__end_height):
            raise InvalidParamsException(f"{self.__address} is not P-Rep")

    @property
    def address(self):
        return self.__address

    @property
    def penalties(self) -> Dict[int, Penalty]:
        return self.__penalties

    def get_prep(self, height: int) -> Optional[dict]:
        try:
            resp = self.__rpc.get_prep(self.__address, height)
        except JSONRPCException:
            return None
        else:
            return resp

    def is_prep(self, height: int) -> bool:
        return self.get_prep(height) is not None

    def get_penalty(self, height: int) -> Penalty:
        return Penalty.from_string(self.__rpc.get_prep(self.__address, height)["penalty"])

    def run(self):
        low, high = self.__start_height, self.__end_height
        cur_penalty = self.get_penalty(low)
        target_penalty = self.get_penalty(high)

        if cur_penalty == target_penalty:
            return

        # find slashing heights
        while low <= high:
            mid = (low + high) // 2
            penalty = self.get_penalty(mid)
            if cur_penalty != penalty:
                prev_penalty = self.get_penalty(mid - 1)
                if cur_penalty == prev_penalty:
                    # mid-1 is penalty height
                    self.__penalties[mid-1] = ~cur_penalty & penalty
                    if target_penalty == penalty:
                        break
                    # find again from mid
                    low = mid + 1
                    high = self.__end_height
                    cur_penalty = penalty
                    continue
                else:
                    high = mid - 1
            else:
                low = mid + 1

    def get_event(self, signatures: List[str]) -> Dict[int, List]:
        result = {}
        for height in self.__penalties.keys():
            events = []
            block = self.__rpc.sdk.get_block(height)
            tx_result = self.__rpc.sdk.get_transaction_result(block["confirmed_transaction_list"][0]["txHash"])
            for event in tx_result["eventLogs"]:
                indexed = event["indexed"]
                if event["scoreAddress"] == SYSTEM_ADDRESS and indexed[0] in signatures and indexed[1] == self.__address:
                    events.append(event)
            result[height] = events
        return result

    def print_event(self, signatures: List[str]):
        result = self.get_event(signatures)
        for height, events in result.items():
            print(f"At block height {height}: {self.__penalties[height]}")
            for e in events:
                print(f"\t{e}")