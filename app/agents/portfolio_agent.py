from app.agents.state import InvestmentState

def portfolio_agent(state: InvestmentState) -> dict:
    # Educational discussion only. No personal allocation or trade recommendation.
    return {'portfolio': {'topics': ['Cash and liquidity', 'Diversification',
                                    'Equity and bond fund risk', 'Fees and time horizon'],
                          'recommendation': None}}
