#!/usr/bin/env python

# CAVEAT UTILITOR
#
# This file was automatically generated by TatSu.
#
#    https://pypi.python.org/pypi/tatsu/
#
# Any changes you make to it will be overwritten the next time
# the file is generated.

from __future__ import annotations

from typing import Any
from dataclasses import dataclass

from tatsu.objectmodel import Node
from tatsu.semantics import ModelBuilderSemantics


@dataclass(eq=False)
class ModelBase(Node):
    pass


class GameLogicModelBuilderSemantics(ModelBuilderSemantics):
    def __init__(self, context=None, types=None):
        types = [
            t for t in globals().values()
            if type(t) is type and issubclass(t, ModelBase)
        ] + (types or [])
        super().__init__(context=context, types=types)


@dataclass(eq=False)
class VariableNode(ModelBase):
    name: Any = None
    type: Any = None


@dataclass(eq=False)
class SignatureNode(ModelBase):
    name: Any = None
    types: Any = None


@dataclass(eq=False)
class PropositionNode(ModelBase):
    arguments: Any = None
    name: Any = None


@dataclass(eq=False)
class ActionPreconditionNode(ModelBase):
    condition: Any = None
    preserve: Any = None


@dataclass(eq=False)
class ActionNode(ModelBase):
    name: Any = None
    postconditions: Any = None
    preconditions: Any = None


@dataclass(eq=False)
class PlaceholderNode(ModelBase):
    name: Any = None
    type: Any = None


@dataclass(eq=False)
class PredicateNode(ModelBase):
    name: Any = None
    parameters: Any = None


@dataclass(eq=False)
class RulePreconditionNode(ModelBase):
    condition: Any = None
    preserve: Any = None


@dataclass(eq=False)
class RuleNode(ModelBase):
    name: Any = None
    postconditions: Any = None
    preconditions: Any = None


@dataclass(eq=False)
class AliasNode(ModelBase):
    lhs: Any = None
    rhs: Any = None


@dataclass(eq=False)
class ReverseRuleNode(ModelBase):
    lhs: Any = None
    rhs: Any = None


@dataclass(eq=False)
class PredicatesNode(ModelBase):
    predicates: Any = None


@dataclass(eq=False)
class RulesNode(ModelBase):
    rules: Any = None


@dataclass(eq=False)
class ReverseRulesNode(ModelBase):
    reverse_rules: Any = None


@dataclass(eq=False)
class ConstraintsNode(ModelBase):
    constraints: Any = None


@dataclass(eq=False)
class Inform7TypeNode(ModelBase):
    definition: Any = None
    kind: Any = None


@dataclass(eq=False)
class Inform7PredicateNode(ModelBase):
    predicate: Any = None
    source: Any = None


@dataclass(eq=False)
class Inform7PredicatesNode(ModelBase):
    predicates: Any = None


@dataclass(eq=False)
class Inform7CommandNode(ModelBase):
    command: Any = None
    event: Any = None
    rule: Any = None


@dataclass(eq=False)
class Inform7CommandsNode(ModelBase):
    commands: Any = None


@dataclass(eq=False)
class Inform7CodeNode(ModelBase):
    code: Any = None


@dataclass(eq=False)
class Inform7Node(ModelBase):
    parts: Any = None


@dataclass(eq=False)
class TypeNode(ModelBase):
    name: Any = None
    parts: Any = None
    supertypes: Any = None


@dataclass(eq=False)
class DocumentNode(ModelBase):
    types: Any = None


@dataclass(eq=False)
class ActionTemplateNode(ModelBase):
    template: Any = None


@dataclass(eq=False)
class ActionFeedbackNode(ModelBase):
    name: Any = None


@dataclass(eq=False)
class ActionPddlNode(ModelBase):
    code: Any = None


@dataclass(eq=False)
class ActionGrammarNode(ModelBase):
    code: Any = None


@dataclass(eq=False)
class ActionTypeNode(ModelBase):
    feedback: Any = None
    grammar: Any = None
    name: Any = None
    pddl: Any = None
    template: Any = None


@dataclass(eq=False)
class PddlDocumentNode(ModelBase):
    parts: Any = None


@dataclass(eq=False)
class ExpressionNode(ModelBase):
    expression: Any = None


@dataclass(eq=False)
class ConjunctionNode(ModelBase):
    expressions: Any = None


@dataclass(eq=False)
class DisjunctionNode(ModelBase):
    expressions: Any = None
