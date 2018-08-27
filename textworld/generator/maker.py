# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import os
from os.path import join as pjoin

from typing import List, Iterable, Union, Optional
try:
    from typing import Collection
except ImportError:
    # Collection is new in Python 3.6 -- fall back on Iterable for 3.5
    from typing import Iterable as Collection

import textworld

from textworld.utils import make_temp_directory

from textworld.generator import data, user_query
from textworld.generator.vtypes import get_new
from textworld.logic import State, Variable, Proposition, Action
from textworld.generator.chaining import get_failing_constraints
from textworld.generator.game import Game, World, Quest, WorldEntity, WorldPath, WorldRoom, WorldRoomExit
from textworld.generator.graph_networks import DIRECTIONS
from textworld.render import visualize
from textworld.envs.wrappers import Recorder


class MissingPlayerError(ValueError):
    pass


class PlayerAlreadySetError(ValueError):
    pass


class FailedConstraintsError(ValueError):
    """
    Thrown when a constraint has failed during generation.
    """

    def __init__(self, failed_constraints: List[Action]) -> None:
        """
        Args:
            failed_constraints: The constraints that have failed
        """
        msg = "The following constraints have failed: "
        msg += ", ".join(set(action.name for action in failed_constraints))
        super().__init__(msg)

    
class GameMaker:
    """ Stateful utility class for handcrafting text-based games.

    Attributes:
        player (WorldEntity): Entity representing the player.
        inventory (WorldEntity): Player's envi entity.
        rooms (List[WorldRoom]): The rooms present in this world.
    """

    def __init__(self) -> None:
        """
        Creates an empty world, with a player and an empty inventory.
        """
        self._world = World()
        # self._entities = {}
        self._quests = []
        # self.rooms = []
        # self.paths = []
        # self._types_counts = data.get_types().count(State())
        # self.player = self.new(type='P')
        # self.inventory = self.new(type='I')
        self.grammar = textworld.generator.make_grammar()
        self._game = None
        # self._distractors_facts = []
    
    @property
    def world(self) -> State:
        """ World being built. """
        return self._world
    
    @property
    def inventory(self) -> WorldEntity:
        """ Player's inventory. """
        return self.world.inventory

    def add_fact(self, name: str, *entities: List[WorldEntity]) -> None:
        """ Adds a fact.

        Args:
            name: The name of the new fact.
            *entities: A list of `WorldEntity` as arguments to this fact.
        """
        entities[0].add_fact(name, *entities)

    def new_door(self, path: WorldPath, name: Optional[str] = None,
                 desc: Optional[str] = None) -> WorldEntity:
        """ Creates a new door and add it to the path.

        Args:
            path: A path between two rooms where to add the door.
            name: The name of the door. Default: generate one automatically.
            desc: The description of the door.

        Returns:
            The newly created door.
        """
        path.door = self.world.new(type='d', name=name, desc=desc)
        return path.door

    def new_room(self, name: Optional[str] = None,
                 desc: Optional[str] = None) -> WorldRoom:
        """ Create new room entity.

        Args:
            name: The name of the room.
            desc: The description of the room.

        Returns:
            The newly created room entity.
        """
        return self.world.new(type='r', name=name, desc=desc)

    def new(self, type: str, name: Optional[str] = None,
            desc: Optional[str] = None) -> Union[WorldEntity, WorldRoom]:
        """ Creates new entity given its type.

        Args:
            type: The type of the entity.
            name: The name of the entity.
            desc: The description of the entity.

        Returns:
            The newly created entity.

            * If the `type` is `'r'`, then a `WorldRoom` object is returned.
            * Otherwise, a `WorldEntity` is returned.
        """
        return self.world.new(type, name, desc)

    def findall(self, type: str) -> List[WorldEntity]:
        """ Gets all entities of the given type.

        Args:
            type: The type of entity to find.

        Returns:
            All entities which match.
        """
        entities = []
        for entity in self.world._entities.values():
            if entity.type == type:
                entities.append(entity)

        return entities

    def set_player(self, room: WorldRoom) -> None:
        """ Place the player in room.

        Args:
            room: The room the player will start in.

        Notes:
            At the moment, the player can only be place once and
            cannot be moved once placed.

        Raises:
            PlayerAlreadySetError: If the player has already been set.
        """
        if self.world.player in self.world:
            raise PlayerAlreadySetError()

        room.add(self.world.player)

    def connect(self, exit1: WorldRoomExit, exit2: WorldRoomExit) -> WorldPath:
        """ Connect two rooms using their exits.

        Args:
            exit1: The exit of the first room to link.
            exit2: The exit of the second room to link.

        Returns:
            The path created by the link between two rooms, with no door.
        """
        return self.world.connect(exit1, exit2)

    # def add_distractors(self, nb_distractors: int) -> None:
    #     """ Adds a number of distractors - random objects.

    #     Args:
    #         nb_distractors: The number of distractors to add.
    #     """
    #     self._distractors_facts = []
    #     world = World.from_facts(self.facts)
    #     self._distractors_facts = world.populate(nb_distractors)

    def new_quest(self, max_length: int) -> Quest:
        """ Generates a random quest for the game.

        Calling this method replaced all previous quests.

        Args:
            max_length: The maximum length of the quest to generate.

        Returns:
            The generated quest.
        """
        world = World.from_facts(self.world.facts)
        self._quests = [textworld.generator.make_quest(world, max_length)]

        # Calling build will generate the description for the quest.
        self.build()
        return self._quests[0]

    def test(self) -> None:
        """ Test the game being built.

        This launches a `textworld.play` session.
        """
        with make_temp_directory() as tmpdir:
            game_file = self.compile(pjoin(tmpdir, "test_game"))
            textworld.play(game_file)

    def record_quest(self, ask_for_state: bool = False) -> Quest:
        """ Defines the game's quest by recording the commands.

        This launches a `textworld.play` session.

        Args:
            ask_for_state: If true, the user will be asked to specify
                           which set of facts of the final state are
                           should be true in order to consider the quest
                           as completed.

        Returns:
            The resulting quest.
        """
        with make_temp_directory() as tmpdir:
            game_file = self.compile(pjoin(tmpdir, "record_quest"))
            recorder = Recorder()
            textworld.play(game_file, wrapper=recorder)

        # Skip "None" actions.
        actions = [action for action in recorder.actions if action is not None]

        # Ask the user which quests have important state, if this is set
        # (if not, we assume the last action contains all the relevant facts)
        winning_facts = None
        if ask_for_state and recorder.last_game_state is not None:
            winning_facts = user_query.query_for_important_facts(actions=recorder.actions,
                                                                 facts=recorder.last_game_state.state.facts,
                                                                 varinfos=self._working_game.infos)

        self._quests = [Quest(actions=actions, winning_conditions=winning_facts)]
        # Calling build will generate the description for the quest.
        self.build()

        return self._quests[0]

    def set_quest_from_commands(self, commands: List[str], ask_for_state: bool = False) -> Quest:
        """ Defines the game's quest using predefined text commands.

        This launches a `textworld.play` session.

        Args:
            commands: Text commands.
            ask_for_state: If true, the user will be asked to specify
                           which set of facts of the final state are
                           should be true in order to consider the quest
                           as completed.

        Returns:
            The resulting quest.
        """
        with make_temp_directory() as tmpdir:
            try:
                game_file = self.compile(pjoin(tmpdir, "record_quest"))
                recorder = Recorder()
                agent = textworld.agents.WalkthroughAgent(commands)
                textworld.play(game_file, agent=agent, wrapper=recorder, silent=True)
            except textworld.agents.WalkthroughDone:
                pass  # Quest is done.

        # Skip "None" actions.
        actions = [action for action in recorder.actions if action is not None]

        # Ask the user which quests have important state, if this is set
        # (if not, we assume the last action contains all the relevant facts)
        winning_facts = None
        if ask_for_state and recorder.last_game_state is not None:
            winning_facts = user_query.query_for_important_facts(actions=recorder.actions,
                                                                 facts=recorder.last_game_state.state.facts,
                                                                 varinfos=self._working_game.infos)

        self._quests = [Quest(actions=actions, winning_conditions=winning_facts)]

        # Calling build will generate the description for the quest.
        self.build()
        return self._quests[0]

    def set_quest_from_final_state(self, final_state: Collection[Proposition]) -> Quest:
        """ Defines the game's quest using a collection of facts.

        The quest will be considered as finished as soon as all the provided
        facts are true.

        Args:
            final_state: List of all facts that will have to be true for
                         the quest to be considered as completed.

        Returns:
            The resulting quest.
        """
        quest = Quest(actions=None, winning_conditions=final_state)
        self._quests = [quest]

        # Calling build will generate the description for the quest
        self.build()
        return self._quests[0]

    def validate(self) -> bool:
        """ Check if the world is valid and can be compiled.

        A world is valid is the player has been place in a room and
        all constraints (defined in the :ref:`knowledge base <KB>`)
        are respected.
        """
        if self.world.player not in self.world:
            msg = "Player position has not been specified. Use 'M.set_player(room)'."
            raise MissingPlayerError(msg)

        failed_constraints = get_failing_constraints(self.world.state)
        if len(failed_constraints) > 0:
            raise FailedConstraintsError(failed_constraints)

        return True

    def build(self, validate: bool = True) -> Game:
        """ Create a `Game` instance given the defined facts.

        Parameters
        ----------
        validate : optional
            If True, check if the game is valid, i.e. respects all constraints.

        Returns
        -------
            Generated game.
        """
        if validate:
            self.validate()  # Validate the state of the world.

        #world = World.from_facts(self.world.facts)
        game = Game(self.world, quests=self._quests)

        # Keep names and descriptions that were manually provided.
        for k, var_infos in game.infos.items():
            if k in self.world._entities:
                var_infos.name = self.world._entities[k].name
                var_infos.desc = self.world._entities[k].desc

            # If we can, reuse information generated during last build.
            if self._game is not None and k in self._game.infos:
                # var_infos.desc = self._game.infos[k].desc
                var_infos.name = self._game.infos[k].name
                var_infos.adj = self._game.infos[k].adj
                var_infos.noun = self._game.infos[k].noun
                var_infos.room_type = self._game.infos[k].room_type

        # Generate text for recently added objects.
        game.change_grammar(self.grammar)
        game.metadata["desc"] = "Generated with textworld.GameMaker."

        self._game = game  # Keep track of previous build.
        return self._game

    def compile(self, name: str) -> str:
        """
        Compile this game.

        Parameters
        ----------
        name :
            Name of the generated game file (without extension).

        Returns
        -------
        game_file
            Path to the game file.
        """
        self._working_game = self.build()
        games_folder = os.path.dirname(os.path.abspath(name))
        game_name = os.path.basename(os.path.splitext(name)[0])
        game_file = textworld.generator.compile_game(self._working_game, game_name, force_recompile=True, games_folder=games_folder)
        return game_file

    def render(self, interactive: bool = False):
        """
        Returns a visual representation of the world.
        :param interactive: opens an interactive session in the browser instead of returning a png.
        :return:
        :param save_screenshot: ONLY FOR WHEN interactive == False. Save screenshot in temp directory.
        :param filename: filename for screenshot
        """
        game = self.build(validate=False)
        game.change_grammar(self.grammar)  # Generate missing object names.
        return visualize(game, interactive=interactive)

