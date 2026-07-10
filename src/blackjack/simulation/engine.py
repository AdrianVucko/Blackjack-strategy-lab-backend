"""Play a single blackjack round end-to-end using a decision policy.

The engine ties the framework-agnostic core (cards, hand, dealer play,
settlement) to a player policy (default: basic strategy) and returns the net
result in units of the base bet.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from blackjack.core.cards import Card, Shoe
from blackjack.core.enums import Action
from blackjack.core.hand import Hand
from blackjack.core.rules import Rules, play_dealer, resolve
from blackjack.strategy import decide

Policy = Callable[..., Action]


@dataclass(slots=True)
class _LiveHand:
    hand: Hand
    wager: float
    surrendered: bool = False


@dataclass(slots=True)
class RoundResult:
    net: float
    num_hands: int


def _dealer_has_hole_blackjack(dealer: Hand) -> bool:
    upcard = dealer.cards[0]
    peeks = upcard.rank.is_ace or upcard.rank.points == 10
    return peeks and dealer.is_blackjack


def _play_player_hands(
    initial: Hand,
    dealer_up: Card,
    shoe: Shoe,
    rules: Rules,
    policy: Policy,
) -> list[_LiveHand]:
    completed: list[_LiveHand] = []
    stack: list[_LiveHand] = [_LiveHand(initial, wager=1.0)]
    splits_done = 0

    while stack:
        live = stack.pop()
        hand = live.hand

        if len(hand) == 1:
            hand.add(shoe.deal())

        # Split aces receive exactly one card and cannot act further.
        if hand.from_split and hand.cards[0].rank.is_ace:
            completed.append(live)
            continue

        while True:
            can_split = (
                hand.is_pair
                and len(hand) == 2
                and splits_done < rules.max_splits
                and (rules.resplit_allowed or splits_done == 0)
            )
            action = policy(hand, dealer_up, rules, can_split=can_split)

            if action is Action.STAND:
                completed.append(live)
                break
            if action is Action.SURRENDER:
                live.surrendered = True
                completed.append(live)
                break
            if action is Action.HIT:
                hand.add(shoe.deal())
                if hand.is_bust:
                    completed.append(live)
                    break
                continue
            if action is Action.DOUBLE:
                hand.add(shoe.deal())
                live.wager *= 2
                completed.append(live)
                break
            if action is Action.SPLIT:
                splits_done += 1
                first, second = hand.cards
                stack.append(_LiveHand(Hand([first], from_split=True), wager=live.wager))
                stack.append(_LiveHand(Hand([second], from_split=True), wager=live.wager))
                break

    return completed


def play_round(shoe: Shoe, rules: Rules, *, policy: Policy = decide) -> RoundResult:
    """Play one round from the current shoe and return the net (in base-bet units)."""
    player = Hand([shoe.deal()])
    dealer = Hand([shoe.deal()])
    player.add(shoe.deal())
    dealer.add(shoe.deal())

    if _dealer_has_hole_blackjack(dealer):
        _, net = resolve(player, dealer, rules)
        return RoundResult(net=net, num_hands=1)

    if player.is_blackjack:
        _, net = resolve(player, dealer, rules)
        return RoundResult(net=net, num_hands=1)

    completed = _play_player_hands(player, dealer.cards[0], shoe, rules, policy)

    any_live = any(not lh.surrendered and not lh.hand.is_bust for lh in completed)
    if any_live:
        play_dealer(dealer, shoe, rules)

    net = 0.0
    for lh in completed:
        _, hand_net = resolve(
            lh.hand, dealer, rules, wager=lh.wager, surrendered=lh.surrendered
        )
        net += hand_net

    return RoundResult(net=net, num_hands=len(completed))
