# Note: This code is for interpreting the point names to the actual coordinates.

# Define the INTERPRETER with placeholders for xbasic and ybasic
INTERPRETER = {
    # Inlet Position
    'i1': "((xbasic*0), (-ybasic*4))",

    #Row 1 (ABC)
    '1A': "((xbasic*0.5), (-ybasic*4))",
    '1B': "((xbasic*1.5), (-ybasic*4))",
    '1C': "((xbasic*2.5), (-ybasic*4))",

    #Row 2 (ABC)
    '2A': "((xbasic*0.5), (-ybasic*3))",
    '2B': "((xbasic*1.5), (-ybasic*3))",
    '2C': "((xbasic*2.5), (-ybasic*3))",

    #Row 3 (ABC)
    '3A': "((xbasic*0.5), (-ybasic*2))",
    '3B': "((xbasic*1.5), (-ybasic*2))",
    '3C': "((xbasic*2.5), (-ybasic*2))",

    #Row 4 (ABC)
    '4A': "((xbasic*0.5), (-ybasic*1))",
    '4B': "((xbasic*1.5), (-ybasic*1))",
    '4C': "((xbasic*2.5), (-ybasic*1))",

    #Row 5 (ABC)
    '5A': "((xbasic*0.5), (ybasic*0))",
    '5B': "((xbasic*1.5), (ybasic*0))",
    '5C': "((xbasic*2.5), (ybasic*0))",

    #Row 6 (ABC)
    '6A': "((xbasic*0.5), (ybasic*1))",
    '6B': "((xbasic*1.5), (ybasic*1))",
    '6C': "((xbasic*2.5), (ybasic*1))",

    #Row 7 (ABC)
    '7A': "((xbasic*0.5), (ybasic*2))",
    '7B': "((xbasic*1.5), (ybasic*2))",
    '7C': "((xbasic*2.5), (ybasic*2))",

    #Row 8 (ABC)
    '8A': "((xbasic*0.5), (ybasic*3))",
    '8B': "((xbasic*1.5), (ybasic*3))",
    '8C': "((xbasic*2.5), (ybasic*3))",

    #Row 9 (ABC)
    '9A': "((xbasic*0.5), (ybasic*4))",
    '9B': "((xbasic*1.5), (ybasic*4))",
    '9C': "((xbasic*2.5), (ybasic*4))",

    # Outlet Position
    'o1': "((xbasic*0), (ybasic*4))",
}

# Basic Point Sets for iGenerator
def get_points_sets(xbasic, ybasic):
    """Basic point sets for iGenerator"""
    return {
        'points': [((xbasic*0), (-ybasic*4)), ((xbasic*0.5), (-ybasic*4)), ((xbasic*0.5), (-ybasic*3)), ((xbasic*2.5), (-ybasic*3)), ((xbasic*2.5), (ybasic*3)), ((xbasic*0.5), (ybasic*3)), ((xbasic*0.5), (ybasic*4)), ((xbasic*0), (ybasic*4))],
    }

