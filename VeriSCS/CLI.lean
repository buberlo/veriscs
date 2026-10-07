import OAI.Computability.Superstring.Main

/-!
Text interface for `OAI.Superstring.answer`.

Each input line is one string. Each Unicode scalar value becomes one symbol,
encoded as 21 bits, most significant bit first (the width of a Unicode scalar,
`0` … `0x10FFFF`). The verified function is then called on that
`OAI.Superstring.Instance`. The symbol sequence it returns is decoded with the
same map and written to standard output, followed by a single newline.

The encoding and this executable are not part of the machine-checked statement.
`answer_spec` applies to the encoded instance: the output is a common
superstring in the symbol alphabet, of length at most twice the optimum
measured in symbols. For this encoding, symbol length is the number of Unicode
scalar values.
-/

open OAI.Superstring

/-- Bits per symbol. Every Unicode scalar fits in 21 bits. -/
def symbolBits : Nat := 21

def encodeChar (c : Char) : Symbol :=
  (List.range symbolBits).map fun i => Nat.testBit c.toNat (symbolBits - 1 - i)

def encodeString (s : String) : Word :=
  s.toList.map encodeChar

def bitsToNat (bs : List Bool) : Nat :=
  bs.foldl (fun acc b => acc * 2 + (bif b then 1 else 0)) 0

def decodeChar (bs : Symbol) : Except String Char := do
  if bs.length != symbolBits then
    throw s!"symbol has {bs.length} bits; this interface only decodes {symbolBits}-bit symbols"
  let n := bitsToNat bs
  if n.isValidChar then
    return Char.ofNat n
  else
    throw s!"bit pattern {n} is not a Unicode scalar value"

def decodeWord (w : Word) : Except String String := do
  let mut chars : List Char := []
  for sym in w do
    chars := chars ++ [← decodeChar sym]
  return String.ofList chars

/-- Split on `\n` only. A trailing `\r` on a line is removed. A final empty
line produced by a terminating newline is dropped; empty lines in the middle
are kept as empty strings. -/
def linesOf (text : String) : List String :=
  let rec go (cs : List Char) (cur : List Char) (acc : List (List Char)) : List (List Char) :=
    match cs with
    | [] => (cur.reverse :: acc).reverse
    | '\n' :: rest => go rest [] (cur.reverse :: acc)
    | c :: rest => go rest (c :: cur) acc
  let raw := (go text.toList [] []).map fun line =>
    let line := match line.getLast? with
      | some '\r' => line.dropLast
      | _ => line
    String.ofList line
  match raw.getLast? with
  | some "" => raw.dropLast
  | _ => raw

def readInput (path? : Option String) : IO String := do
  match path? with
  | none => (← IO.getStdin).readToEnd
  | some path => IO.FS.readFile path

structure Options where
  roundtrip : Bool := false
  stats : Bool := false
  path? : Option String := none

def usage : String :=
  "usage: veriscs [--roundtrip] [--stats] [FILE]\n\
   \n\
   Read strings, one per line, from FILE or from standard input.\n\
   Encode each Unicode scalar as a 21-bit symbol and print the common\n\
   superstring produced by OAI.Superstring.answer.\n\
   \n\
   --roundtrip  encode and decode the input without running the algorithm\n\
   --stats      write `symbols: N` to standard error\n"

def parseArgs (args : List String) : Except String Options := do
  let rec go (args : List String) (opt : Options) (sawPath : Bool) : Except String Options := do
    match args with
    | [] => return opt
    | "--help" :: _ | "-h" :: _ => throw usage
    | "--roundtrip" :: rest => go rest {opt with roundtrip := true} sawPath
    | "--stats" :: rest => go rest {opt with stats := true} sawPath
    | "--" :: rest =>
      match rest with
      | [] => return opt
      | [p] => if sawPath then throw usage else return {opt with path? := some p}
      | _ => throw usage
    | p :: rest =>
      if p.startsWith "-" && p != "-" then
        throw usage
      else if sawPath then
        throw usage
      else
        let path? := if p = "-" then none else some p
        go rest {opt with path? := path?} true
  go args {} false

def main (args : List String) : IO UInt32 := do
  let opt ← match parseArgs args with
    | .ok opt => pure opt
    | .error msg =>
      IO.eprintln msg
      return 1
  let text ← readInput opt.path?
  let lines := linesOf text
  if opt.roundtrip then
    for line in lines do
      match decodeWord (encodeString line) with
      | .ok s =>
        if s != line then
          IO.eprintln "roundtrip mismatch"
          return 1
        IO.println s
      | .error e =>
        IO.eprintln e
        return 1
    return 0
  let instance_ : Instance := lines.map encodeString
  let encoded := answer instance_
  match decodeWord encoded with
  | .error e =>
    IO.eprintln s!"decoder rejected the algorithm output: {e}"
    IO.eprintln "The verified function returned a symbol outside the 21-bit Unicode encoding."
    return 2
  | .ok text =>
    if opt.stats then
      IO.eprintln s!"symbols: {encoded.length}"
    IO.println text
    return 0
