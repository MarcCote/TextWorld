# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.


import io
import json
import tempfile
from os.path import join as pjoin
from typing import Union, Dict, Optional

import numpy as np
import networkx as nx

import textworld
from textworld.logic import Variable, Proposition, Action
from textworld.envs.glulx.git_glulx_ml import GlulxGameState
from textworld.logic import State
from textworld.generator import World, Game
from textworld.generator.graph_networks import relative_2d_constraint_layout
from textworld.utils import maybe_mkdir, get_webdriver

from textworld.generator.game import EntityInfo
from textworld.generator import data


def load_state_from_game_state(game_state: GlulxGameState) -> dict:
    """
    Generates serialization of game state.

    Args:
        game_state: The current game state to visualize.
    
    Returns:
        A JSON serializable object ready to be rendered.
    """
    game_infos = game_state.game_infos
    game_infos["objective"] = game_state.objective
    last_action = game_state.action

    # Create a world from the current state's facts.
    world = World.from_facts(game_state.state.facts)
    return load_state(world, game_infos, last_action)


def load_state(world: World, game_infos: Optional[Dict[str, EntityInfo]] = None, action: Optional[Action] = None) -> dict:    
    """
    Generates serialization of a world.

    Args:
        world: The current state of the world to visualize.
        game_infos: The mapping needed to get objects names.
        action: If provided, highlight the world changes made by that action.
    
    Returns:
        A JSON serializable object ready to be rendered.
    """
    room = world.player_room or world.rooms[0]

    G = nx.Graph()
    constraints = []
    G.add_nodes_from(room.id for room in world.rooms)

    def is_positioning_fact(proposition: Proposition):
        return proposition.name in ["north_of", "south_of", "east_of", "west_of"]

    positioning_facts = [fact for fact in world.facts if is_positioning_fact(fact)]
    for fact in positioning_facts:
        G.add_edge(fact.arguments[0].name, fact.arguments[1].name)
        constraints.append((fact.arguments[0].name, fact.name[:-3], fact.arguments[1].name))

    pos = relative_2d_constraint_layout(G, constraints)
    #pos = {game_infos[k].name: v for k, v in pos.items()}

    result = {}
    # Objective
    # if "objective" in game_infos:
    #     result["objective"] = game_infos["objective"]

    world_data = world.serialize()
    result["inventory"] = world_data["inventory"]
    result["rooms"] = world_data["rooms"]
    for room in result["rooms"]:
        room["position"] = pos[room["id"]]
        

    def _get_displayed_name_from_id(entity_id, game_infos):
        if entity_id in game_infos and game_infos[entity_id].name is not None:
            return game_infos[entity_id].name

        return entity_id


    def _get_displayed_name(entity, game_infos):
        return _get_displayed_name_from_id(entity["id"], game_infos)


    # Use entity names from game_infos.
    entities = list(result["rooms"]) + [result["inventory"]]
    while len(entities) > 0:
        entity = entities.pop()
        entities += entity["contents"]
        entity["name"] = _get_displayed_name(entity, game_infos)

        entity["portable"] = data.get_types().is_descendant_of(entity["type"], "o")

        entity["infos"] = ""
        for fact in entity["facts"]:
            if fact["name"] == "match":
                entity["infos"] += " (for {})".format(_get_displayed_name_from_id(fact["arguments"][-1]["name"], game_infos))

    def _get_door(edge):
        for fact in world.facts:
            if fact.name != "link":
                continue
            
            if fact.arguments[0].name == edge[0] and fact.arguments[-1].name == edge[1]:
                return [obj.serialize() for obj in world.objects if obj.id == fact.arguments[1].name][0]
        
        return None

    result["connections"] = [{"source": game_infos[e[0]].name, "target": game_infos[e[1]].name, 'door': _get_door(e)} for e in G.edges]
    return result


def take_screenshot(url: str, id: str='graph2'):
    """
    Takes a screenshot of DOM element given its id.
    :param url: URL of webpage to open headlessly.
    :param id: ID of DOM element.
    :return: Image object.
    """
    from PIL import Image

    driver = get_webdriver()

    driver.get(url)
    svg = driver.find_element_by_id(id)
    location = svg.location
    size = svg.size
    png = driver.get_screenshot_as_png()

    driver.close()
    image = Image.open(io.BytesIO(png))
    left = location['x']
    top = location['y']
    right = location['x'] + size['width']
    bottom = location['y'] + size['height']
    image = image.crop((left, top, right, bottom))
    return image


def visualize(world: Union[Game, State, GlulxGameState, World],
              interactive: bool = False):
    """
    Show the current state of the world.
    :param world: Object representing a game state to be visualized.
    :param interactive: Whether or not to visualize the state in the browser.
    :return: Image object of the visualization.
    """
    try:
        import webbrowser
    except ImportError:
        raise ImportError('Visualization dependencies not installed. Try running `pip install textworld[vis]`')

    if isinstance(world, Game):
        game = world
        state = load_state(game.world, game.infos)
        state["objective"] = ""
        if len(game.quests) > 0:
            state["objective"] = game.quests[0].desc
    elif isinstance(world, GlulxGameState):
        state = load_state_from_game_state(game_state=world)
    elif isinstance(world, World):
        state = load_state(world)
    elif isinstance(world, State):
        state = world
        world = World.from_facts(state.facts)
        state = load_state(world)
    else:
        raise ValueError("Don't know how to visualize: {!r}".format(world))

    state["command"] = ""
    state["history"] = ""
    from textworld.render.serve import get_html_template
    html = get_html_template(game_state=json.dumps(state))
    tmpdir = maybe_mkdir(pjoin(tempfile.gettempdir(), "textworld"))
    fh, filename = tempfile.mkstemp(suffix=".html", dir=tmpdir, text=True)
    url = 'file://' + filename
    with open(filename, 'w') as f:
        f.write(html)

    image = take_screenshot(url)
    if interactive:
        try:
            webbrowser.open(url)
        finally:
            return image

    return image
