from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race, Difficulty
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from loguru import logger


class FightBot(BotAI):
    def __init__(self):
        super().__init__()
        self.control_received = False
        self.fight_started = False

    async def on_step(self, iteration):
        # retrieve control by enabling enemy control and showing whole map
        if iteration == 0:
            # we need this one for `self.enemy_units` to "see" all units on the map
            await self._client.debug_show_map()
            # this one will allow us to do something like: `self.enemy_units.first.attack(self._game_info.map_center)`
            await self._client.debug_control_enemy()

        # wait till control retrieved
        if iteration > 0 and self.enemy_units and not self.control_received:
            # prepare my side
            me = 1

            cc = self.townhalls.first
            p = cc.position.towards(self.game_info.map_center, 4)
            # create supply
            await self._client.debug_create_unit([[UnitTypeId.SUPPLYDEPOT, 1, p, me]])
            # destroy command center
            await self._client.debug_kill_unit([cc.tag])
            # destroy all workers
            await self._client.debug_kill_unit([w.tag for w in self.workers])

            # create marines
            await self._client.debug_create_unit([[UnitTypeId.MARINE, 4, p, me]])

            # prepare opponent side
            pc = 2
            cc = self.enemy_structures.first
            p = cc.position.towards(self.game_info.map_center, 4)
            # create supply
            await self._client.debug_create_unit([[UnitTypeId.SUPPLYDEPOT, 1, p, pc]])
            # destroy command center
            await self._client.debug_kill_unit([cc.tag])
            # destroy all workers
            await self._client.debug_kill_unit([w.tag for w in self.enemy_units(UnitTypeId.SCV)])
            # create marines
            await self._client.debug_create_unit([[UnitTypeId.MARINE, 4, p, pc]])
            logger.info("control received")
            # await self.chat_send("control received")
            self.control_received = True

        # note: we should wait till workers will be destroyed
        if not self.fight_started and self.control_received and self.enemy_units and not self.enemy_units(UnitTypeId.SCV) and not self.units(UnitTypeId.SCV):
            # start fight
            for u in self.enemy_units:
                u.attack(self.structures.first.position)
            for u in self.units:
                u.attack(self.enemy_structures.first.position)
            # await self._client.move_camera(self._game_info.map_center)
            logger.info("fight started")
            # await self.chat_send("fight started")
            self.fight_started = True

        # in case of no units left - do not wait for game to finish
        if self.fight_started and (not self.units or not self.enemy_units):
            logger.info("LOSE" if not self.units else "WIN")
            await self._client.quit()  # await self._client.debug_leave() # or reset level

        for u in self.units(UnitTypeId.MARINE):
            u.attack(self.enemy_structures.first.position)
            # TODO: implement your fight logic here
            # if u.weapon_cooldown:
            #     u.move(u.position.towards(self.structures.first.position))
            # else:
            #     u.attack(self.enemy_structures.first.position)
            # pass


def main():
    run_game(
        maps.get("Flat64"),
        # NOTE: you can have to bots fighting with each other here
        [Bot(Race.Terran, FightBot()), Computer(Race.Terran, Difficulty.Medium)],
        realtime=True
    )


if __name__ == "__main__":
    main()
