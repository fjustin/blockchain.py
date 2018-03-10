# coding: UTF-8

import hashlib
import json
from textwrap import dedent
from time import time
# ハッシュキャッシュ実装のためのモジュール
from uuid import uuid4

from flask import Flask,jsonify,request


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # ジェネシスブロックを作る
        self.new_block(previous_hash = 1, proof = 100)

    def new_block(self,proof,previous_hash = None):
        # 新しいブロックを作り、チェーンに加える
        """
        ブロックチェーンに新しいブロックを作る
        :params proof: <int> プルーフ・オブ・ワークアルゴリズムから得られるプルーフ
        :params previous_hash: （オプション）<str> 前のブロックのハッシュ
        :return: <dict> 新しいブロック
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transaction': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # 現在のトランザクションリストをセット
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self,sender,recipient,amount):
        # 新しいトランザクションをリストに加える

        """
        次に採掘されるブロックに加える新しいトランザクションを作る
        :params sender: <str> 送信者のアドレス
        :params recipient: <str> 受信者のアドレス
        :params amount: <int> 量
        :return: <int> このトランザクションを含むブロックのアドレス
        """

        self.current_transactions.append({
            'sender' : sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    def proof_of_work(self,last_proof):
        """
        シンプルなプルーフオブワークのアルゴリズム:
        - hash(pp')の最初の4つが0となるようなp'を探す
        - p は1つ前のブロックのプルーフ、p' は新しいブロックのプルーフ
        :params last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof,proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof,proof):
        """
        プルーフが正しいかどうか確認する: hash(last_proof,proof)の最初の4つが0となっているか？
        :params last_proof: <int> 前のプルーフ
        :params proof: <int> 現在のプルーフ
        :return: <bool> 正しければtrue、そうでなければfalse
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        # ここでtrueかfalseを返す
        return guess_hash[:4] == "0000"


    @property
    # 読み取り専用。Rubyのattr_readerと同じ役割
    def last_block(self):
        # チェーンの最後のブロックをリターンする
        return self.chain[-1]

    @staticmethod
    # クラスの引数を直接返すメソッド
    def hash(block):
        """
        ブロックのSHA-256 ハッシュを作る
        :params block: <dict> ブロック
        :return: <str>
        """
        # 必ずディクショナリがソートされている必要がある。そうでないと一貫性のないハッシュを生成することになる
        block_string = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(block_string).hexdigest()


# ノードを作る
app = Flask(__name__)

# このノードのグローバルにユニークなアドレスを付与する
node_indentifire = str(uuid4()).replace('-','')

# ブロックチェーンのクラスをインスタンス化する
blockchain = Blockchain()

# メソッドはPOSTで/transactions/newエンドポイントを作る。メソッドはPOSTなのでデータを送信する
@app.route('/transactions/new',methods=['POST'])
def new_transactions():
    values = request.get_json()

    # POSTされたデータに必要なデータがあるか確認
    required = ['sender','recipient','amount']

    if not all(k in values for k in required):
        return 'Missing values',400

    # 新しいトランザクションを作る
    index = blockchain.new_transaction(values['sender'],values['recipient'],values['amount'])

    response = {'message':f'トランザクションはブロック{index}に追加されました'}
    return jsonify(response),201

# メソッドはGETで/mineエンドポイントを作る
@app.route('/mine',methods=['GET'])
def mine():
    # 次のプルーフを見つけるためプルーフオブワークアルゴリズムを使用する
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # プルーフを見つけたことに対する報酬を得る
    # 送信者は、採掘者が新しいコインを採掘したことを表すために"0"とする
    blockchain.new_transaction(
        sender = "0",
        recipient = node_indentifire,
        amount=1,
    )

    # チェーンにブロックを追加することで新しいブロックを採掘する
    block = blockchain.new_block(proof)

    response = {
        'message': '新しいブロックを採掘しました',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response),200

# メソッドはGETで、フルのブロックチェーンをリターンする/chainエンドポイントを作る
@app.route('/chein',methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

# port5000でサーバーを起動する
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
