from app.workflows.investment_graph import build_graph

if __name__ == '__main__':
    graph = build_graph()
    result = graph.invoke({
        'customer_id': 'CUST-003',
        'query': 'How should I invest given my aggressive risk tolerance and moderate risk capacity?'
    })
    print('\nINTENT:', result['intent'])
    print('CUSTOMER FOUND:', result['customer']['found'])
    print('MONTHLY SURPLUS:', result['risk']['monthly_surplus'])
    print('KNOWLEDGE SOURCES:', result['knowledge']['sources'])
    print('COMPLIANCE:', result['compliance'])
    print('STATUS:', result['status'])
    print('RESPONSE:', result['response'])
    assert result['customer']['found']
    assert result['risk']['monthly_surplus'] == 6500.0
    assert result['status'] == 'needs_review'
    assert result['compliance']['human_review_required']
    print('\nTEST PASSED')
