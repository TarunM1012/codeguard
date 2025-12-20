#definind github's diff (difference) format
def parse_patch(patch):
    """
    Parse a GitHub patch/diff into individual changes
    
    Patch looks like:
    @@ -10,3 +10,5 @@
     unchanged line
    -deleted line
    +added line
     unchanged line
    """
#if no patch return empty list
    if not patch:
        return []
    
    changes = []
    lines = patch.split('\n')
    
    current_line = 0
#convert patch into list of lines
    for line in lines:
        # Line number header: @@ -10,3 +10,5 @@
        if line.startswith('@@'):
            # Extract new file line number
            parts = line.split('+')[1].split('@@')[0].strip()
            current_line = int(parts.split(',')[0])
            continue
        
        # Added line
        #if it starts with + and not +++ then it's an addition
        if line.startswith('+') and not line.startswith('+++'):
            changes.append({
                'type': 'addition',
                'line': current_line,
                'content': line[1:]  # Remove the '+'
            })
            current_line += 1
        
        # Deleted line
        elif line.startswith('-') and not line.startswith('---'):
            changes.append({
                'type': 'deletion',
                'content': line[1:]  # Remove the '-'
            })
        
        # Unchanged line
        elif line.startswith(' '):
            current_line += 1
    
    return changes

def extract_added_code(patch):
    """Get just the new code that was added"""
    changes = parse_patch(patch)
    added_lines = [c['content'] for c in changes if c['type'] == 'addition']
    return '\n'.join(added_lines)

# Test it
if __name__ == "__main__":
    test_patch = """@@ -10,3 +10,5 @@
 def divide(a, b):
-    return a / b
+    if b == 0:
+        return None
+    return a / b
"""
    
    print("Parsing test patch:")
    changes = parse_patch(test_patch)
    
    for change in changes:
        print(f"{change['type']}: {change['content']}")
    
    print("\nAdded code only:")
    print(extract_added_code(test_patch))